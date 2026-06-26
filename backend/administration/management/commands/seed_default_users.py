"""Create the default role-based logins requested for the system."""

from datetime import date
from typing import cast

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from administration.models import Student, Staff, User as SchoolUser
from portals.models import ParentPortalAccess, StudentPortalAccess


User = cast(type[SchoolUser], get_user_model())


class Command(BaseCommand):
    help = 'Create default user accounts for the main system roles.'

    def handle(self, *args, **options):
        accounts = [
            {
                'username': 'Manager',
                'first_name': 'Manager',
                'last_name': 'User',
                'user_type': 'manager',
                'profile_kind': 'staff',
                'staff_type': 'manager',
            },
            {
                'username': 'HeadTeacher',
                'first_name': 'Head',
                'last_name': 'Teacher',
                'user_type': 'head_teacher',
                'profile_kind': 'staff',
                'staff_type': 'head_teacher',
            },
            {
                'username': 'Teacher',
                'first_name': 'Teacher',
                'last_name': 'User',
                'user_type': 'teacher',
                'profile_kind': 'staff',
                'staff_type': 'teacher',
            },
            {
                'username': 'Auxilery',
                'first_name': 'Auxiliary',
                'last_name': 'User',
                'user_type': 'auxiliary',
                'profile_kind': 'staff',
                'staff_type': 'auxiliary',
            },
            {
                'username': 'Parent',
                'first_name': 'Parent',
                'last_name': 'User',
                'user_type': 'parent',
                'profile_kind': 'parent',
            },
            {
                'username': 'Student',
                'first_name': 'Student',
                'last_name': 'User',
                'user_type': 'student',
                'profile_kind': 'student',
            },
        ]

        parent_user = None
        student_user = None

        for account in accounts:
            user, created = User.objects.get_or_create(
                username=account['username'],
                defaults={
                    'first_name': account['first_name'],
                    'last_name': account['last_name'],
                    'user_type': account['user_type'],
                    'is_active': True,
                    'is_staff': account['user_type'] in {'manager', 'head_teacher', 'teacher', 'auxiliary'},
                },
            )

            user.first_name = account['first_name']
            user.last_name = account['last_name']
            user.user_type = account['user_type']
            user.is_active = True
            user.is_staff = account['user_type'] in {'manager', 'head_teacher', 'teacher', 'auxiliary'}
            user.set_password('1234')
            user.save()

            if account['profile_kind'] == 'staff':
                Staff.objects.update_or_create(
                    user=user,
                    defaults={
                        'staff_id': f"{account['username'].upper()}-001",
                        'staff_type': account['staff_type'],
                        'employment_type': 'full_time',
                        'date_of_joining': date.today(),
                        'department': 'General',
                        'designation': account['first_name'],
                        'qualification': 'N/A',
                        'experience_years': 0,
                        'gender': 'O',
                        'is_active': True,
                    },
                )

            if account['profile_kind'] == 'parent':
                parent_user = user
                ParentPortalAccess.objects.get_or_create(parent=user)

            if account['profile_kind'] == 'student':
                student_user = user

        if student_user is not None:
            student_profile, _ = Student.objects.update_or_create(
                user=student_user,
                defaults={
                    'admission_number': 'ADM-0001',
                    'admission_date': date.today(),
                    'current_class': None,
                    'gender': 'O',
                    'blood_group': '',
                    'nationality': 'Nigerian',
                    'religion': '',
                    'parent': parent_user,
                    'guardian_name': parent_user.get_full_name() if parent_user else 'Parent User',
                    'guardian_relationship': 'Parent',
                    'guardian_phone': parent_user.phone_number if parent_user and parent_user.phone_number else '+0000000000',
                    'guardian_email': parent_user.email if parent_user else '',
                    'guardian_address': 'Not provided',
                    'medical_conditions': '',
                    'is_active': True,
                    'status': 'active',
                },
            )
            StudentPortalAccess.objects.get_or_create(student=student_profile)

        self.stdout.write(self.style.SUCCESS('Default accounts created or updated successfully.'))
        self.stdout.write('Login passwords have been set to 1234 for all six accounts.')