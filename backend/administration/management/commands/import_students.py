"""
Management command to bulk import students from CSV/Excel files
Usage: python manage.py import_students <file_path>
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from administration.models import Student, ClassRoom, Grade
import csv
import openpyxl
from datetime import datetime
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Bulk import students from CSV or Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or Excel file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test the import without saving to database',
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue importing even if some records fail',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']

        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            students_data = self.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            students_data = self.read_excel(file_path)
        else:
            raise CommandError('Unsupported file format. Use CSV or Excel (.xlsx, .xls)')

        self.stdout.write(self.style.SUCCESS(f'Found {len(students_data)} student records'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        success_count = 0
        error_count = 0
        errors = []

        for idx, student_data in enumerate(students_data, start=1):
            try:
                if dry_run:
                    self.validate_student_data(student_data)
                    self.stdout.write(f'✓ Row {idx}: Valid - {student_data.get("first_name")} {student_data.get("last_name")}')
                else:
                    self.create_student(student_data)
                    self.stdout.write(self.style.SUCCESS(f'✓ Row {idx}: Created - {student_data.get("first_name")} {student_data.get("last_name")}'))
                success_count += 1
            except Exception as e:
                error_count += 1
                error_msg = f'✗ Row {idx}: ERROR - {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
                if not skip_errors:
                    raise CommandError(f'Import stopped at row {idx}. Use --skip-errors to continue.')

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
            self.stdout.write('\nError details:')
            for error in errors:
                self.stdout.write(self.style.ERROR(error))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No changes made to database'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Import complete! {success_count} students added.'))

    def read_csv(self, file_path):
        """Read student data from CSV file"""
        students = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                students.append(row)
        return students

    def read_excel(self, file_path):
        """Read student data from Excel file"""
        students = []
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        # Get headers from first row
        headers = [cell.value for cell in sheet[1]]

        # Read data rows
        for row in sheet.iter_rows(min_row=2, values_only=True):
            student_data = dict(zip(headers, row))
            # Skip empty rows
            if any(student_data.values()):
                students.append(student_data)

        return students

    def validate_student_data(self, data):
        """Validate student data before creation"""
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
        
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f'Missing required field: {field}')

        # Validate gender
        if data.get('gender') not in ['M', 'F', 'Male', 'Female']:
            raise ValueError(f'Invalid gender: {data.get("gender")}. Use M/F or Male/Female')

        # Validate class if provided
        if data.get('class_name'):
            try:
                ClassRoom.objects.get(name=data['class_name'])
            except ClassRoom.DoesNotExist:
                raise ValueError(f'Class not found: {data["class_name"]}')

        return True

    @transaction.atomic
    def create_student(self, data):
        """Create student and user account from data"""
        
        # Validate first
        self.validate_student_data(data)

        # Normalize gender
        gender = data['gender']
        if gender in ['Male', 'M']:
            gender = 'M'
        elif gender in ['Female', 'F']:
            gender = 'F'

        # Parse date of birth
        dob = data['date_of_birth']
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                try:
                    dob = datetime.strptime(dob, '%d/%m/%Y').date()
                except ValueError:
                    raise ValueError(f'Invalid date format: {dob}. Use YYYY-MM-DD or DD/MM/YYYY')

        # Generate username
        username = f"{data['first_name'].lower()}.{data['last_name'].lower()}"
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user account
        user = User.objects.create_user(
            username=username,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', ''),
            password=data.get('password', 'password123'),  # Default password
            user_type='student'
        )

        # Get class if provided
        current_class = None
        if data.get('class_name'):
            current_class = ClassRoom.objects.get(name=data['class_name'])

        # Create student profile
        student = Student.objects.create(
            user=user,
            date_of_birth=dob,
            gender=gender,
            current_class=current_class,
            address=data.get('address', ''),
            phone_number=data.get('phone_number', ''),
            emergency_contact=data.get('emergency_contact', ''),
            blood_group=data.get('blood_group', ''),
            religion=data.get('religion', ''),
            nationality=data.get('nationality', 'Nigerian'),
        )

        return student
