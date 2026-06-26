"""
Quick setup script to create sample data for the School Management System
Run this after creating a superuser
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from administration.models import AcademicYear, Term, Grade, ClassRoom, Student, Staff, SchoolInformation
from academics.models import Subject
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for the school management system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create School Information
        school, created = SchoolInformation.objects.get_or_create(
            school_name='Demo High School',
            defaults={
                'school_code': 'DHS001',
                'motto': 'Excellence in Education',
                'email': 'info@demohigh.edu',
                'phone': '+2348012345678',
                'address': '123 Education Street, Lagos, Nigeria',
                'principal_name': 'Dr. John Smith',
                'principal_phone': '+2348087654321',
                'principal_email': 'principal@demohigh.edu',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ School information created'))
        
        # Create Academic Year
        current_year = date.today().year
        academic_year, created = AcademicYear.objects.get_or_create(
            name=f'{current_year}/{current_year + 1}',
            defaults={
                'start_date': date(current_year, 9, 1),
                'end_date': date(current_year + 1, 6, 30),
                'is_current': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Academic year {academic_year.name} created'))
        
        # Create Terms
        terms_data = [
            ('First Term', date(current_year, 9, 1), date(current_year, 12, 15), True),
            ('Second Term', date(current_year + 1, 1, 6), date(current_year + 1, 3, 30), False),
            ('Third Term', date(current_year + 1, 4, 20), date(current_year + 1, 6, 30), False),
        ]
        
        for term_name, start, end, is_current in terms_data:
            term, created = Term.objects.get_or_create(
                academic_year=academic_year,
                term_number=term_name,
                defaults={
                    'start_date': start,
                    'end_date': end,
                    'is_current': is_current
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ {term_name} created'))
        
        # Create Grades
        for i in range(1, 7):  # Grades 1-6
            grade, created = Grade.objects.get_or_create(
                name=f'Grade {i}',
                defaults={'level': i}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Grade {i} created'))
            
            # Create Classes for each grade
            for section in ['A', 'B']:
                classroom, created = ClassRoom.objects.get_or_create(
                    grade=grade,
                    section=section,
                    academic_year=academic_year,
                    defaults={
                        'room_number': f'{i}0{ord(section) - 64}',
                        'capacity': 30
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Class {grade.name}-{section} created'))
        
        # Create Subjects
        subjects = [
            ('Mathematics', 'MATH'),
            ('English', 'ENG'),
            ('Science', 'SCI'),
            ('Social Studies', 'SST'),
            ('Physical Education', 'PE'),
            ('Arts', 'ART'),
            ('Computer Science', 'CS'),
        ]
        
        for name, code in subjects:
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Subject {name} created'))
        
        # Create sample teacher user
        if not User.objects.filter(username='teacher').exists():
            teacher_user = User.objects.create_user(
                username='teacher',
                password='teacher123',
                first_name='Jane',
                last_name='Doe',
                email='teacher@demohigh.edu',
                user_type='teacher',
                phone_number='+2348011111111'
            )
            
            Staff.objects.create(
                user=teacher_user,
                employee_id='TCH001',
                staff_type='teaching',
                position='Senior Teacher',
                department='Mathematics',
                date_of_birth=date(1985, 5, 15),
                date_of_joining=date(2015, 9, 1),
                qualifications='B.Ed Mathematics'
            )
            self.stdout.write(self.style.SUCCESS('✓ Sample teacher created (username: teacher, password: teacher123)'))
        
        # Create sample student user
        if not User.objects.filter(username='student').exists():
            student_user = User.objects.create_user(
                username='student',
                password='student123',
                first_name='John',
                last_name='Student',
                email='student@demohigh.edu',
                user_type='student',
                phone_number='+2348022222222'
            )
            
            grade1 = Grade.objects.get(name='Grade 1')
            class1a = ClassRoom.objects.get(grade=grade1, section='A', academic_year=academic_year)
            
            Student.objects.create(
                user=student_user,
                admission_number='STU001',
                admission_date=date.today() - timedelta(days=30),
                current_class=class1a,
                date_of_birth=date(2013, 3, 10),
                gender='M',
                address='456 Student Lane, Lagos',
                guardian_name='Mr. Student Parent',
                guardian_relationship='Father',
                guardian_phone='+2348033333333',
                guardian_email='parent@email.com'
            )
            self.stdout.write(self.style.SUCCESS('✓ Sample student created (username: student, password: student123)'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data creation completed!'))
        self.stdout.write('\nYou can now login with:')
        self.stdout.write('  Teacher - username: teacher, password: teacher123')
        self.stdout.write('  Student - username: student, password: student123')
