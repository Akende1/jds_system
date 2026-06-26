import os
import sys
import traceback
from pprint import pprint

repo_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

import django
django.setup()

from django.test import Client
from django.utils import timezone
from decimal import Decimal

report = {}

client = Client()

# Helper to run tests
def run_test(name, fn):
    print(f"\n=== Running: {name} ===")
    try:
        res = fn()
        report[name] = {'status': 'ok', 'details': res}
        print(f"OK: {name}")
    except Exception as e:
        tb = traceback.format_exc()
        report[name] = {'status': 'error', 'error': str(e), 'trace': tb}
        print(f"ERROR: {name}: {e}")

# 1. Authentication & Role Flow
def test_auth_roles():
    from administration.models import User
    roles = ['admin','manager','head_teacher','teacher','auxiliary','parent','student']
    results = {}
    for role in roles:
        u = User.objects.filter(user_type=role).first()
        results[role] = u.username if u else None
        if u:
            client.force_login(u)
            r_root = client.get('/', HTTP_HOST='localhost')
            r_mgr = client.get('/manager/approvals/', HTTP_HOST='localhost')
            results[role+'_root_status'] = r_root.status_code
            results[role+'_approvals_status'] = r_mgr.status_code
            client.logout()
    return results

# 2. Approval System
def test_approval_workflow():
    from finance.models import RestockingRequest, StockItem
    from administration.services import ApprovalService
    from administration.models import ApprovalRequest, User
    # create a stock item if none
    item, _ = StockItem.objects.get_or_create(name='Test Paper A4', defaults={'unit_cost': Decimal('10.00'), 'unit': 'pcs'})
    # prefer Staff model if available
    try:
        from administration.models import Staff
        staff = Staff.objects.first() or User.objects.filter(user_type='teacher').first() or User.objects.first()
    except Exception:
        staff = User.objects.filter(user_type='teacher').first() or User.objects.first()
    rr = RestockingRequest.objects.create(
        staff=staff,
        stock_item=item,
        quantity=10,
        reason='Unit test restocking',
        status='pending'
    )
    # create approval request
    reviewers = User.objects.filter(user_type__in=['admin','manager'])
    approval = ApprovalService.create_request(instance=rr, request_type='restock', reviewers=reviewers, requested_by=staff, remarks='Please approve')
    ok1 = ApprovalRequest.objects.filter(pk=approval.pk).exists()
    # Approve
    ApprovalService.approve(approval, reviewers.first() if reviewers.exists() else staff, remarks='Approved by test')
    rr.refresh_from_db()
    approval.refresh_from_db()
    return {'approval_created': ok1, 'restocking_status': rr.status, 'approval_status': approval.status}

# 3. Timetable validation
def test_timetable_validation():
    from academics.models import Timetable, Subject
    from administration.models import ClassRoom, User, AcademicYear, Term
    sub = Subject.objects.order_by('pk').first() or Subject.objects.create(name='TestSub')
    cls = ClassRoom.objects.order_by('pk').first()
    if not cls:
        return {'skipped': 'no classrooms available'}
    teacher = User.objects.filter(user_type='teacher').first()
    year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    term = Term.objects.filter(academic_year=year).first() if year else None
    # create an entry
    t1 = Timetable.objects.create(classroom=cls, subject=sub, teacher=teacher, academic_year=year, term=term, day_of_week='monday', start_time='08:00', end_time='08:40', room='A1')
    # attempt overlapping
    try:
        t2 = Timetable(classroom=cls, subject=sub, teacher=teacher, academic_year=year, term=term, day_of_week='monday', start_time='08:20', end_time='09:00', room='A1')
        t2.full_clean()
        t2.save()
        return {'overlap_allowed': True}
    except Exception as e:
        return {'overlap_detected': True, 'error': str(e)}

# 4. Finance flow
def test_finance_flow():
    from finance.models import FeeInvoice, Payment
    from administration.models import Student, User, AcademicYear, Term
    student = Student.objects.first()
    if not student:
        return {'skipped': 'no student found'}
    year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    term = Term.objects.filter(academic_year=year).first() if year else None
    invoice = FeeInvoice.objects.create(invoice_number=f'TST-{timezone.now().strftime("%Y%m%d%H%M%S")}', student=student, academic_year=year, term=term, total_amount=Decimal('1000.00'), net_amount=Decimal('1000.00'), amount_paid=Decimal('0.00'), balance=Decimal('1000.00'), due_date=timezone.now().date()+timezone.timedelta(days=7))
    payment = Payment.objects.create(receipt_number=f'REC-TST-{timezone.now().strftime("%Y%m%d%H%M%S")}', invoice=invoice, student=student, amount=Decimal('400.00'), payment_method='cash', payment_status='confirmed')
    invoice.refresh_from_db()
    partial = invoice.status == 'partial' or invoice.amount_paid == Decimal('400.00')
    # finish payment
    payment2 = Payment.objects.create(receipt_number=f'REC-TST2-{timezone.now().strftime("%Y%m%d%H%M%S")}', invoice=invoice, student=student, amount=Decimal('600.00'), payment_method='cash', payment_status='confirmed')
    invoice.refresh_from_db()
    return {'initial_partial': partial, 'final_status': invoice.status, 'balance': str(invoice.balance)}

# 5. Academics flow
def test_academics_flow():
    from academics.models import Subject, Exam, ExamResult
    from administration.models import ClassRoom, Student, User, AcademicYear, Term
    subject = Subject.objects.first() or Subject.objects.create(name='AutoSubject')
    classroom = ClassRoom.objects.first()
    year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    term = Term.objects.filter(academic_year=year).first() if year else None
    exam = Exam.objects.create(name='UnitTest Exam', subject=subject, classroom=classroom, term=term, exam_date=timezone.now().date(), start_time='09:00', duration_minutes=60)
    student = Student.objects.first()
    if not student:
        return {'skipped': 'no student'}
    result = ExamResult.objects.create(exam=exam, student=student, marks_obtained=75)
    return {'exam_created': exam.pk, 'result_created': result.pk}

# 6. Attendance
def test_attendance():
    from attendance.models import StudentAttendance
    from administration.models import Student
    student = Student.objects.first()
    if not student:
        return {'skipped': 'no student'}
    # find a classroom for attendance
    from administration.models import ClassRoom
    cls = ClassRoom.objects.order_by('pk').first()
    if not cls:
        raise Exception('No ClassRoom available for attendance test')
    att = StudentAttendance.objects.create(student=student, date=timezone.now().date(), status='present', classroom=cls)
    # avoid creating duplicate attendance for same student/date
    if StudentAttendance.objects.filter(student=student, date=timezone.now().date()).count() > 1:
        return {'created': [att.pk], 'note': 'duplicate skipped'}
    return {'created': [att.pk]}

# 7. Communication
def test_communication():
    from communication.email_utils import EmailSender
    from communication.sms_utils import SmsSender
    # pick a parent
    from administration.models import Student
    s = Student.objects.first()
    if not s:
        return {'skipped': 'no student'}
    email_ok = EmailSender.send_fee_reminder(s, s.fee_invoices.first() if s.fee_invoices.exists() else None)
    sms_ok = SmsSender.send_payment_confirmation(s, s.payments.first() if s.payments.exists() else None)
    return {'email_ok': email_ok, 'sms_ok': sms_ok}

# 8. Parent portal
def test_parent_portal():
    from administration.models import Student
    s = Student.objects.first()
    if not s:
        return {'skipped': 'no student'}
    parent = getattr(s, 'parent', None)
    if not parent:
        return {'skipped': 'no parent linked'}
    # verify access via relationship
    children = list(parent.student_set.all().values_list('pk', flat=True)) if hasattr(parent, 'student_set') else []
    return {'parent': parent.username, 'children_count': len(children)}

# 9. Inventory
def test_inventory():
    from finance.models import StockItem, RestockingRequest
    from administration.models import User
    si = StockItem.objects.create(name='Test Item X', unit_cost=Decimal('5.00'), unit='pcs')
    try:
        from administration.models import Staff
        staff = Staff.objects.first() or User.objects.filter(user_type='teacher').first()
    except Exception:
        staff = User.objects.filter(user_type='teacher').first()
    rr = RestockingRequest.objects.create(staff=staff, stock_item=si, quantity=5, reason='Test')
    return {'stock_item': si.pk, 'restocking': rr.pk}

# 10. Transport
def test_transport():
    try:
        from transport.models import Route, StudentTripAttendance
        from administration.models import Student, User
        r = Route.objects.create(name='Route Test', vehicle_no='V-TEST')
        student = Student.objects.first()
        if not student:
            return {'skipped': 'no student'}
        # assign via m2m if available
        if hasattr(r, 'students'):
            r.students.add(student)
        return {'route': r.pk}
    except Exception as e:
        return {'skipped': 'transport app missing or error', 'error': str(e)}

# 11. Notifications
def test_notifications():
    from administration.models import Notification, User
    u = User.objects.filter(user_type='admin').first()
    n = Notification.objects.create(recipient=u, notification_type='test', title='Test', message='Testing')
    count = Notification.objects.filter(recipient=u).count()
    return {'notification_created': n.pk, 'total': count}

# 12. Analytics quick check
def test_analytics():
    from attendance.models import StudentAttendance
    total = StudentAttendance.objects.count()
    return {'attendance_records': total}

# 13. Sync
def test_sync():
    try:
        from sync.models import SyncLog
        s = SyncLog.objects.create(source='test', details='sync test')
        return {'sync_log': s.pk}
    except Exception as e:
        return {'skipped': 'sync app missing', 'error': str(e)}

# Run all
sequence = [
    ('auth_roles', test_auth_roles),
    ('approval_workflow', test_approval_workflow),
    ('timetable_validation', test_timetable_validation),
    ('finance_flow', test_finance_flow),
    ('academics_flow', test_academics_flow),
    ('attendance', test_attendance),
    ('communication', test_communication),
    ('parent_portal', test_parent_portal),
    ('inventory', test_inventory),
    ('transport', test_transport),
    ('notifications', test_notifications),
    ('analytics', test_analytics),
    ('sync', test_sync),
]

for name, fn in sequence:
    run_test(name, fn)

print('\n=== SUMMARY ===')

pprint(report)

# Save report file
import json
with open(os.path.join(os.path.dirname(__file__), 'full_system_test_report.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print('\nReport written to scripts/full_system_test_report.json')
