"""
Management command to bulk generate fee invoices
Usage: python manage.py generate_bulk_fees --month 1 --year 2025 --grade "Grade 1"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from finance.models import FeeStructure, Invoice, Student
from academics.models import Grade
from datetime import datetime, date
from decimal import Decimal


class Command(BaseCommand):
    help = 'Bulk generate fee invoices for students'

    def add_arguments(self, parser):
        parser.add_argument('--month', type=int, required=True, help='Month number (1-12)')
        parser.add_argument('--year', type=int, required=True, help='Year (e.g., 2025)')
        parser.add_argument('--grade', type=str, help='Grade name (e.g., "Grade 1")')
        parser.add_argument('--class', type=str, dest='class_name', help='Specific class name')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test the generation without saving',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip students who already have invoices for this period',
        )

    def handle(self, *args, **options):
        month = options['month']
        year = options['year']
        grade_name = options.get('grade')
        class_name = options.get('class_name')
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

        # Validate month
        if month < 1 or month > 12:
            raise CommandError('Month must be between 1 and 12')

        # Get students
        students = Student.objects.select_related('user', 'current_class', 'current_class__grade').all()

        if grade_name:
            try:
                grade = Grade.objects.get(name=grade_name)
                students = students.filter(current_class__grade=grade)
            except Grade.DoesNotExist:
                raise CommandError(f'Grade not found: {grade_name}')

        if class_name:
            students = students.filter(current_class__name=class_name)

        if not students.exists():
            raise CommandError('No students found matching criteria')

        self.stdout.write(self.style.SUCCESS(f'Found {students.count()} students'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No invoices will be created'))

        success_count = 0
        skip_count = 0
        error_count = 0

        billing_date = date(year, month, 1)

        for student in students:
            try:
                # Check for existing invoice
                if skip_existing:
                    existing = Invoice.objects.filter(
                        student=student,
                        billing_date__year=year,
                        billing_date__month=month
                    ).exists()
                    
                    if existing:
                        skip_count += 1
                        self.stdout.write(f'⊘ Skipped: {student.user.get_full_name()} - Invoice already exists')
                        continue

                if not dry_run:
                    invoice = self.create_invoice(student, billing_date)
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created: {student.user.get_full_name()} - ₦{invoice.total_amount:,.2f} ({invoice.invoice_number})'
                    ))
                else:
                    total = self.calculate_total(student)
                    self.stdout.write(f'✓ Would create: {student.user.get_full_name()} - ₦{total:,.2f}')
                
                success_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Error: {student.user.get_full_name()} - {str(e)}'
                ))

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed: {success_count}'))
        if skip_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (existing): {skip_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Generation complete! {success_count} invoices created.'))

    def calculate_total(self, student):
        """Calculate total fees for student"""
        if not student.current_class:
            raise ValueError(f'Student {student.user.get_full_name()} has no assigned class')

        fee_structures = FeeStructure.objects.filter(
            grade=student.current_class.grade
        )

        if not fee_structures.exists():
            raise ValueError(f'No fee structure found for {student.current_class.grade.name}')

        total = sum(fs.amount for fs in fee_structures)
        return Decimal(str(total))

    @transaction.atomic
    def create_invoice(self, student, billing_date):
        """Create invoice for student"""
        
        total_amount = self.calculate_total(student)

        # Generate invoice number
        year_month = billing_date.strftime('%Y%m')
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year_month}'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f'INV-{year_month}-{new_num:05d}'

        # Create invoice
        invoice = Invoice.objects.create(
            student=student,
            invoice_number=invoice_number,
            billing_date=billing_date,
            due_date=date(billing_date.year, billing_date.month, 25),  # 25th of month
            total_amount=total_amount,
            amount_paid=Decimal('0.00'),
            status='pending'
        )

        return invoice
