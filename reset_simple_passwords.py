#!/usr/bin/env python
"""
Quick password reset script for development.
Sets all test users to password: '1234' for easy testing.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
sys.path.insert(0, 'backend')

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    print("Make sure you're in the project directory and have activated the venv.")
    sys.exit(1)

from django.contrib.auth import get_user_model

User = get_user_model()

# Define simple passwords for development
PASSWORDS = {
    'Manager': '1234',
    'HeadTeacher': '1234',
    'Teacher': '1234',
    'Auxilery': '1234',
    'Parent': '1234',
    'Student': '1234',
}

print("\n" + "="*60)
print("RESETTING TEST USER PASSWORDS")
print("="*60 + "\n")

updated_count = 0
missing_count = 0

for username, password in PASSWORDS.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save(update_fields=['password'])
        print(f"✓ {username:<15} → password set to '{password}'")
        updated_count += 1
    except User.DoesNotExist:
        print(f"✗ {username:<15} → user not found in database")
        missing_count += 1

# Also reset superuser if exists
try:
    admin_user = User.objects.get(username='admin')
    admin_user.set_password('admin1234')
    admin_user.save(update_fields=['password'])
    print(f"✓ admin (superuser)  → password set to 'admin1234'")
    updated_count += 1
except User.DoesNotExist:
    print(f"✗ admin (superuser)  → user not found in database")
    missing_count += 1

print("\n" + "="*60)
print(f"SUMMARY: Updated {updated_count} users, {missing_count} missing")
print("="*60)

if missing_count > 0:
    print("\nTo create missing users, run:")
    print("  python manage.py seed_default_users")

print("\nYou can now login with:")
print("  Username: Manager (or any other user above)")
print("  Password: 1234")
print("\n")
