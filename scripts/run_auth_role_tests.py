import os
import sys
from pprint import pprint

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

import django
django.setup()

from django.test import Client
from administration.models import User

roles = ['admin','manager','head_teacher','teacher','auxiliary','parent','student']

client = Client()

results = {
    'found_users': {},
    'dashboard_checks': [],
    'unauthorized_checks': [],
}

for role in roles:
    user = User.objects.filter(user_type=role).first()
    if user:
        results['found_users'][role] = user.username
    else:
        results['found_users'][role] = None

# For each found user, force_login and request root and manager approvals
for role, username in results['found_users'].items():
    if not username:
        continue
    user = User.objects.get(username=username)
    client.force_login(user)
    resp_root = client.get('/')
    resp_approvals = client.get('/manager/approvals/')

    results['dashboard_checks'].append({
        'role': role,
        'username': username,
        'root_status': resp_root.status_code,
        'root_path': resp_root.request.get('PATH_INFO', ''),
        'root_redirect': resp_root.has_header('Location'),
        'approvals_status': resp_approvals.status_code,
        'approvals_redirect': resp_approvals.has_header('Location'),
    })
    client.logout()

# Unauthorized access: try student accessing manager page
student_username = results['found_users'].get('student')
if student_username:
    student = User.objects.get(username=student_username)
    client.force_login(student)
    resp = client.get('/manager/approvals/')
    results['unauthorized_checks'].append({
        'as_student_status': resp.status_code,
        'redirect': resp.has_header('Location'),
        'content_snippet': resp.content.decode('utf-8')[:300]
    })
    client.logout()

pprint(results)

# Exit code 0
print('\nDone')
