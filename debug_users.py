#!/usr/bin/env python
"""Debug script to inspect live user accounts in the database."""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
sys.path.insert(0, 'backend')

django.setup()

from administration.models import User

print(f"\n{'='*80}")
print("LIVE USER ACCOUNTS IN DATABASE")
print(f"{'='*80}\n")

users = User.objects.all().order_by('username')
print(f"Total Users: {users.count()}\n")
print(f"{'Username':<20} {'User Type':<15} {'Active':<8} {'Staff':<8} {'Superuser':<12}")
print(f"{'-'*20} {'-'*15} {'-'*8} {'-'*8} {'-'*12}")

for u in users:
    print(f"{u.username:<20} {u.user_type:<15} {str(u.is_active):<8} {str(u.is_staff):<8} {str(u.is_superuser):<12}")

print(f"\n{'='*80}\n")
