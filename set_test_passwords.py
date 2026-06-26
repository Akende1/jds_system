#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from administration.models import User

# Define distinct passwords for each role
passwords = {
    'admin': 'Admin1234!',
    'Manager': 'Manager1234!',
    'HeadTeacher': 'HeadTeacher1234!',
    'Teacher': 'Teacher1234!',
    'Auxilery': 'Auxiliary1234!',
    'Parent': 'Parent1234!',
    'Student': 'Student1234!'
}

# Update passwords
print("Setting test passwords for each role type:\n")
for username, password in passwords.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save(update_fields=['password'])
        print(f"✓ {username:15} : {password}")
    except User.DoesNotExist:
        print(f"✗ {username:15} : User not found")

print("\n✓ All test credentials updated successfully!")
