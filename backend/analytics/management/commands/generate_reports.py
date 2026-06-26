"""
Management command to generate and send scheduled reports
Usage: python manage.py generate_reports [--report-type TYPE] [--send-email]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
import os
from datetime import datetime

from analytics.models_schedule import ReportSchedule, ReportLog
from administration.models import Student, Grade, ClassRoom
from finance.models import FeeInvoice, Payment
from attendance.models import StudentAttendance
from administration.utils.excel_exporter import StudentExporter, FeeReportExporter, AttendanceExporter


class Command(BaseCommand):
    help = 'Generate scheduled reports and optionally send via email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            help='Generate specific report type only',
            choices=['student_list', 'fee_summary', 'attendance_summary', 'performance_report', 'comprehensive']
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send reports via email to recipients'
        )
        parser.add_argument(
            '--schedule-id',
            type=int,
            help='Generate report for specific schedule ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate report generation without creating files'
        )

    def handle(self, *args, **options):
        report_type = options.get('report_type')
        send_email = options.get('send_email')
        schedule_id = options.get('schedule_id')
        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No files will be created'))

        # Get schedules to process
        schedules = self._get_schedules(report_type, schedule_id)

        if not schedules:
            self.stdout.write(self.style.WARNING('⚠️  No scheduled reports found to generate'))
            return

        self.stdout.write(self.style.SUCCESS(f'📊 Processing {len(schedules)} scheduled report(s)...'))

        success_count = 0
        failed_count = 0

        for schedule in schedules:
            log = None
            try:
                if dry_run:
                    report_label = getattr(schedule, 'get_report_type_display', lambda: schedule.report_type)()
                    self.stdout.write(f'  Would generate: {schedule.name} ({report_label})')
                    continue

                # Create report log
                log = ReportLog.objects.create(
                    schedule=schedule,
                    report_type=schedule.report_type,
                    status='generating',
                    recipients=schedule.recipients
                )

                # Generate report
                file_path = self._generate_report(schedule)

                if file_path and os.path.exists(file_path):
                    # Update log with file info
                    log.file_path = file_path
                    log.file_size = os.path.getsize(file_path)
                    log.status = 'completed'
                    log.completed_at = timezone.now()
                    log.save()

                    self.stdout.write(self.style.SUCCESS(f'  ✅ Generated: {schedule.name}'))
                    self.stdout.write(f'     File: {file_path} ({log.get_file_size_display()})')

                    # Send email if requested
                    if send_email and schedule.recipients:
                        email_sent = self._send_email(schedule, log, file_path)
                        if email_sent:
                            log.email_sent = True
                            log.email_sent_at = timezone.now()
                            log.status = 'sent'
                            log.save()
                            self.stdout.write(self.style.SUCCESS(f'     📧 Email sent to {len(schedule.get_recipient_list())} recipient(s)'))
                        else:
                            self.stdout.write(self.style.WARNING(f'     ⚠️  Email sending failed'))

                    # Update schedule's next run
                    schedule.last_run = timezone.now()
                    schedule.calculate_next_run()

                    success_count += 1
                else:
                    raise Exception('Report file was not created')

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'  ❌ Failed: {schedule.name} - {str(e)}'))
                
                if not dry_run and log is not None:
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = timezone.now()
                    log.save()

        # Summary
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✅ Successfully generated: {success_count}'))
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_count}'))

    def _get_schedules(self, report_type, schedule_id):
        """Get schedules to process"""
        if schedule_id:
            return ReportSchedule.objects.filter(id=schedule_id)
        
        queryset = ReportSchedule.objects.filter(is_active=True)
        
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        else:
            # Get schedules due to run
            queryset = queryset.filter(next_run__lte=timezone.now()) | queryset.filter(next_run__isnull=True)
        
        return queryset

    def _generate_report(self, schedule):
        """Generate report based on schedule configuration"""
        # Create reports directory
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{schedule.report_type}_{timestamp}.xlsx"
        file_path = os.path.join(reports_dir, filename)

        # Build queryset based on filters
        if schedule.report_type == 'student_list':
            queryset = Student.objects.all()
            if schedule.filter_grade:
                queryset = queryset.filter(current_class__grade__name=schedule.filter_grade)
            if schedule.filter_class:
                queryset = queryset.filter(current_class__section=schedule.filter_class)
            
            exporter = StudentExporter()
            exporter.export(queryset)
            exporter.save(file_path)

        elif schedule.report_type == 'fee_summary':
            queryset = FeeInvoice.objects.all()
            if schedule.filter_date_from:
                queryset = queryset.filter(issue_date__gte=schedule.filter_date_from)
            if schedule.filter_date_to:
                queryset = queryset.filter(issue_date__lte=schedule.filter_date_to)
            if schedule.filter_grade:
                queryset = queryset.filter(student__current_class__grade__name=schedule.filter_grade)
            
            exporter = FeeReportExporter()
            exporter.export(queryset)
            exporter.save(file_path)

        elif schedule.report_type == 'attendance_summary':
            queryset = StudentAttendance.objects.all()
            if schedule.filter_date_from:
                queryset = queryset.filter(date__gte=schedule.filter_date_from)
            if schedule.filter_date_to:
                queryset = queryset.filter(date__lte=schedule.filter_date_to)
            if schedule.filter_class:
                queryset = queryset.filter(student__current_class__section=schedule.filter_class)
            
            exporter = AttendanceExporter()
            exporter.export(queryset)
            exporter.save(file_path)

        elif schedule.report_type == 'comprehensive':
            # Generate comprehensive report with multiple sheets
            file_path = self._generate_comprehensive_report(schedule, reports_dir, timestamp)

        else:
            raise ValueError(f'Unknown report type: {schedule.report_type}')

        return file_path

    def _generate_comprehensive_report(self, schedule, reports_dir, timestamp):
        """Generate comprehensive report with multiple sheets"""
        from openpyxl import Workbook
        
        filename = f"comprehensive_report_{timestamp}.xlsx"
        file_path = os.path.join(reports_dir, filename)
        
        wb = Workbook()
        if wb.active is not None:
            wb.remove(wb.active)  # Remove default sheet
        
        # Add students sheet
        students = Student.objects.all()
        if schedule.filter_grade:
            students = students.filter(current_class__grade__name=schedule.filter_grade)
        
        exporter = StudentExporter()
        ws_students = wb.create_sheet('Students')
        exporter._write_students_to_sheet(students, ws_students)
        
        # Add fees sheet
        invoices = FeeInvoice.objects.all()
        if schedule.filter_date_from:
            invoices = invoices.filter(issue_date__gte=schedule.filter_date_from)
        if schedule.filter_date_to:
            invoices = invoices.filter(issue_date__lte=schedule.filter_date_to)
        
        exporter = FeeReportExporter()
        ws_fees = wb.create_sheet('Fees')
        exporter._write_fees_to_sheet(invoices, ws_fees)
        
        # Add attendance sheet
        attendance = StudentAttendance.objects.all()
        if schedule.filter_date_from:
            attendance = attendance.filter(date__gte=schedule.filter_date_from)
        if schedule.filter_date_to:
            attendance = attendance.filter(date__lte=schedule.filter_date_to)
        
        exporter = AttendanceExporter()
        ws_attendance = wb.create_sheet('Attendance')
        exporter._write_attendance_to_sheet(attendance, ws_attendance)
        
        wb.save(file_path)
        return file_path

    def _send_email(self, schedule, log, file_path):
        """Send report via email"""
        try:
            subject = schedule.email_subject or f"Scheduled Report: {schedule.name}"
            body = schedule.email_body or f"Please find attached the {schedule.get_report_type_display()} report."
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=schedule.get_recipient_list()
            )
            
            # Attach file
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                email.attach(filename, f.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            email.send()
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Email error: {str(e)}'))
            return False
