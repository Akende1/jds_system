"""
Management command to promote students in bulk
Usage: python manage.py promote_students --from-class "Grade 1A" --to-class "Grade 2A" [--auto-approve]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from administration.models import ClassRoom, Student, AcademicYear
from administration.models_class_management import ClassPromotion


class Command(BaseCommand):
    help = 'Promote students from one class to another in bulk'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-grade',
            type=str,
            help='Promote all students from this grade (e.g., "Grade 1")'
        )
        parser.add_argument(
            '--from-class',
            type=str,
            help='Promote all students from this specific class (e.g., "Grade 1A")'
        )
        parser.add_argument(
            '--to-grade',
            type=str,
            help='Target grade for promotion (e.g., "Grade 2")'
        )
        parser.add_argument(
            '--to-class',
            type=str,
            help='Target class for promotion (e.g., "Grade 2A")'
        )
        parser.add_argument(
            '--academic-year',
            type=str,
            help='Academic year name (defaults to current)'
        )
        parser.add_argument(
            '--min-percentage',
            type=float,
            default=50.0,
            help='Minimum percentage required for promotion (default: 50)'
        )
        parser.add_argument(
            '--min-attendance',
            type=float,
            default=75.0,
            help='Minimum attendance percentage required (default: 75)'
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Auto-approve all promotions (skip pending status)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate promotion without creating records'
        )

    def handle(self, *args, **options):
        from_grade = options.get('from_grade')
        from_class = options.get('from_class')
        to_grade = options.get('to_grade')
        to_class = options.get('to_class')
        academic_year_name = options.get('academic_year')
        min_percentage = options.get('min_percentage')
        min_attendance = options.get('min_attendance')
        auto_approve = options.get('auto_approve')
        dry_run = options.get('dry_run')

        # Validation
        if not (from_class or from_grade):
            self.stdout.write(self.style.ERROR('❌ Error: Must specify --from-class or --from-grade'))
            return

        if not (to_class or to_grade):
            self.stdout.write(self.style.ERROR('❌ Error: Must specify --to-class or --to-grade'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No records will be created'))

        # Get academic year
        if academic_year_name:
            try:
                academic_year = AcademicYear.objects.get(name=academic_year_name)
            except AcademicYear.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Academic year "{academic_year_name}" not found'))
                return
        else:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
            if not academic_year:
                self.stdout.write(self.style.ERROR('❌ No current academic year found'))
                return

        self.stdout.write(self.style.SUCCESS(f'📚 Academic Year: {academic_year.name}'))

        # Get source students
        students = Student.objects.filter(is_active=True)
        
        if from_class:
            # Specific class
            try:
                from_classroom = ClassRoom.objects.get(
                    grade__name__icontains=from_class.split()[0],  # e.g., "Grade 1"
                    section=from_class[-1],  # e.g., "A"
                    academic_year=academic_year
                )
                students = students.filter(current_class=from_classroom)
                self.stdout.write(f'📍 From: {from_classroom}')
            except ClassRoom.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Class "{from_class}" not found'))
                return
        else:
            # Entire grade
            students = students.filter(current_class__grade__name=from_grade)
            self.stdout.write(f'📍 From Grade: {from_grade}')

        if not students.exists():
            self.stdout.write(self.style.WARNING('⚠️  No students found in source class/grade'))
            return

        self.stdout.write(f'👥 Found {students.count()} students to promote')

        # Get target class(es)
        if to_class:
            # Specific target class
            try:
                to_classroom = ClassRoom.objects.get(
                    grade__name__icontains=to_class.split()[0],
                    section=to_class[-1],
                    academic_year=academic_year
                )
                self.stdout.write(f'📍 To: {to_classroom}')
                
                # Promote all to same class
                self._promote_students(
                    students, to_classroom, academic_year, 
                    min_percentage, min_attendance, auto_approve, dry_run
                )
            except ClassRoom.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Target class "{to_class}" not found'))
                return
        else:
            # Promote to next grade (same section)
            self.stdout.write(f'📍 To Grade: {to_grade}')
            self._promote_by_grade(
                students, to_grade, academic_year, 
                min_percentage, min_attendance, auto_approve, dry_run
            )

    def _promote_students(self, students, to_classroom, academic_year, 
                         min_percentage, min_attendance, auto_approve, dry_run):
        """Promote students to a specific target class"""
        success_count = 0
        failed_count = 0

        with transaction.atomic():
            for student in students:
                if student.current_class == to_classroom:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  {student} already in {to_classroom}, skipping'))
                    continue

                if dry_run:
                    self.stdout.write(f'  Would promote: {student} ({student.current_class} → {to_classroom})')
                    success_count += 1
                    continue

                try:
                    # Check if promotion already exists
                    existing = ClassPromotion.objects.filter(
                        student=student,
                        academic_year=academic_year
                    ).first()

                    if existing:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  {student} already has a promotion record, skipping'))
                        continue

                    # Create promotion
                    promotion = ClassPromotion.objects.create(
                        student=student,
                        from_class=student.current_class,
                        to_class=to_classroom,
                        academic_year=academic_year,
                        final_percentage=min_percentage,  # TODO: Get actual performance data
                        attendance_percentage=min_attendance,  # TODO: Calculate actual attendance
                    )

                    if auto_approve:
                        # Auto-approve and complete
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        admin_user = User.objects.filter(user_type='admin', is_active=True).first()
                        if admin_user:
                            promotion.approve(admin_user)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Promoted: {student} ({promotion.from_class} → {promotion.to_class})'))
                        else:
                            self.stdout.write(self.style.WARNING(f'  ⚠️  Created promotion for {student} but no admin user found for approval'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Created promotion: {student} (Pending approval)'))

                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f'  ❌ Failed: {student} - {str(e)}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully processed: {success_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_count}'))

    def _promote_by_grade(self, students, to_grade, academic_year, 
                         min_percentage, min_attendance, auto_approve, dry_run):
        """Promote students to next grade (preserve section)"""
        success_count = 0
        failed_count = 0

        with transaction.atomic():
            for student in students:
                current_class = student.current_class
                if not current_class:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  {student} has no current class, skipping'))
                    continue

                # Find corresponding class in target grade (same section)
                try:
                    to_classroom = ClassRoom.objects.get(
                        grade__name=to_grade,
                        section=current_class.section,
                        academic_year=academic_year
                    )
                except ClassRoom.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'  ❌ No matching class found: {to_grade}{current_class.section}'))
                    failed_count += 1
                    continue

                if dry_run:
                    self.stdout.write(f'  Would promote: {student} ({current_class} → {to_classroom})')
                    success_count += 1
                    continue

                try:
                    # Check existing promotion
                    existing = ClassPromotion.objects.filter(
                        student=student,
                        academic_year=academic_year
                    ).first()

                    if existing:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  {student} already has a promotion record, skipping'))
                        continue

                    # Create promotion
                    promotion = ClassPromotion.objects.create(
                        student=student,
                        from_class=current_class,
                        to_class=to_classroom,
                        academic_year=academic_year,
                        final_percentage=min_percentage,
                        attendance_percentage=min_attendance,
                    )

                    if auto_approve:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        admin_user = User.objects.filter(user_type='admin', is_active=True).first()
                        if admin_user:
                            promotion.approve(admin_user)
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Promoted: {student} ({promotion.from_class} → {promotion.to_class})'))
                        else:
                            self.stdout.write(self.style.WARNING(f'  ⚠️  Created promotion for {student} but no admin user found'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Created promotion: {student} (Pending approval)'))

                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f'  ❌ Failed: {student} - {str(e)}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully processed: {success_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_count}'))
