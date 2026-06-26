"""
Role-based dashboard views with real-time data
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from typing import Any, cast
from datetime import date, timedelta
from .decorators import *
from .models import Student, User, ClassRoom, AcademicYear, Term
from academics.models import Exam, ExamResult, Assignment
from finance.models import FeeInvoice, Payment, FeeStructure, LunchAttendance
from transport.models import StudentTripAttendance, Route
from django.apps import apps
from attendance.models import StudentAttendance, StaffAttendance
from communication.models import Announcement
from sync.models import SyncLog
from django.contrib import messages
from django.shortcuts import redirect
from .models import EditRequest, Notification, ApprovalRequest


@login_required
def dashboard_router(request):
    """Route users to appropriate dashboard based on role"""
    role = request.user.user_type
    
    dashboard_map = {
        'admin': manager_dashboard,
        'manager': manager_dashboard,
        'head_teacher': head_teacher_dashboard,
        'teacher': teacher_dashboard,
        'auxiliary': auxiliary_dashboard,
        'parent': parent_dashboard,
        'student': student_dashboard,
    }
    
    dashboard_func = dashboard_map.get(role)
    if dashboard_func:
        return dashboard_func(request)
    
    # Fallback - show manager dashboard for superusers
    if request.user.is_superuser:
        return manager_dashboard(request)
    
    return render(request, 'dashboards/default.html')


@manager_required
def manager_dashboard(request):
    """School Manager / Proprietor Dashboard"""
    today = date.today()
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(academic_year=current_year, is_current=True).first() if current_year else None
    
    # Enrollment stats
    total_students = Student.objects.filter(status='active').count()
    new_students_this_term = Student.objects.filter(
        admission_date__gte=current_term.start_date if current_term else today
    ).count()
    
    # Finance stats
    total_invoiced = FeeInvoice.objects.filter(
        academic_year=current_year
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_collected = Payment.objects.filter(
        payment_date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_outstanding = FeeInvoice.objects.filter(
        academic_year=current_year
    ).aggregate(total=Sum('balance'))['total'] or 0
    
    collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
    
    # Potential Earnings (Active Students * Fee Structure)
    potential_revenue = 0
    if current_year and current_term:
        active_students = Student.objects.filter(status='active')
        fee_map = {}
        for fee_structure in FeeStructure.objects.filter(academic_year=current_year).select_related('grade'):
            grade_id = getattr(fee_structure, 'grade_id', None) or getattr(getattr(fee_structure, 'grade', None), 'pk', None)
            if grade_id is not None:
                fee_map[grade_id] = fee_structure.amount
        for student in active_students.select_related('current_class'):
            current_class = student.current_class
            grade_id = getattr(current_class, 'grade_id', None) or getattr(getattr(current_class, 'grade', None), 'pk', None)
            if grade_id is not None and grade_id in fee_map:
                potential_revenue += fee_map[grade_id]

    # Teacher attendance
    teachers = User.objects.filter(user_type='teacher', is_active=True).count()
    present_teachers = StaffAttendance.objects.filter(
        date=today,
        status='present'
    ).count()
    
    # Recent payments
    recent_payments = Payment.objects.select_related(
        'student', 'invoice'
    ).order_by('-payment_date')[:10]
    
    # System alerts
    alerts = []
    
    # Check for sync issues
    failed_syncs = SyncLog.objects.filter(
        status='failed',
        started_at__gte=today - timedelta(days=1)
    ).count()
    if failed_syncs > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'fa-sync',
            'message': f'{failed_syncs} sync failures in last 24 hours'
        })
    
    # Check for overdue invoices
    overdue_count = FeeInvoice.objects.filter(
        due_date__lt=today,
        balance__gt=0
    ).count()
    if overdue_count > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-exclamation-triangle',
            'message': f'{overdue_count} overdue invoices'
        })
    
    context = {
        'total_students': total_students,
        'new_students': new_students_this_term,
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'potential_revenue': potential_revenue,
        'collection_rate': collection_rate,
        'teachers': teachers,
        'present_teachers': present_teachers,
        'recent_payments': recent_payments,
        'alerts': alerts,
        'current_year': current_year,
        'current_term': current_term,
    }
    
    return render(request, 'dashboards/manager.html', context)


@head_teacher_or_manager
def head_teacher_dashboard(request):
    """Head Teacher Dashboard"""
    today = date.today()
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(academic_year=current_year, is_current=True).first() if current_year else None
    
    # Attendance summary
    total_students = Student.objects.filter(status='active').count()
    present_today = StudentAttendance.objects.filter(
        date=today,
        status='present'
    ).count()
    absent_today = StudentAttendance.objects.filter(
        date=today,
        status='absent'
    ).count()
    
    attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
    
    # Class performance (average across recent exams)
    class_performance = ExamResult.objects.filter(
        exam__term=current_term
    ).values('student__current_class__grade__name').annotate(
        avg_score=Avg('marks_obtained')
    ).order_by('-avg_score')[:10]
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        exam_date__gte=today,
        term=current_term
    ).order_by('exam_date')[:5]
    
    # Teacher coverage (who is absent)
    absent_teachers = StaffAttendance.objects.filter(
        date=today,
        status='absent'
    ).select_related('staff')
    
    # Discipline alerts (recent incidents)
    from attendance.models import DisciplineIncident
    recent_incidents = DisciplineIncident.objects.filter(
        date__gte=today - timedelta(days=7)
    ).order_by('-date')[:5]
    
    context = {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
        'class_performance': class_performance,
        'upcoming_exams': upcoming_exams,
        'absent_teachers': absent_teachers,
        'recent_incidents': recent_incidents,
        'current_year': current_year,
        'current_term': current_term,
    }
    
    return render(request, 'dashboards/head_teacher.html', context)


@teacher_or_above
def teacher_dashboard(request):
    """Teacher Dashboard"""
    today = date.today()
    teacher = request.user
    
    # Today's lessons (classes assigned to this teacher)
    from .models_class_management import TeacherAssignment
    teacher_classes = TeacherAssignment.objects.filter(
        teacher=teacher,
        academic_year__is_current=True
    ).select_related('classroom')
    
    # Pending attendance (classes not marked today)
    pending_attendance = []
    for assignment in teacher_classes:
        attendance_marked = StudentAttendance.objects.filter(
            date=today,
            classroom=assignment.classroom
        ).exists()
        if not attendance_marked:
            pending_attendance.append(assignment.classroom)
    
    # Assignments due for marking
    assignments_to_mark = Assignment.objects.filter(
        teacher=teacher,
        due_date__lte=today
    ).annotate(
        submissions_count=Count('submissions')
    )
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        subject__in=teacher_classes.values_list('subject_name', flat=True),
        exam_date__gte=today
    ).order_by('exam_date')[:5]
    
    # Recent messages from parents
    from communication.models import Message
    recent_messages = Message.objects.filter(
        recipient=teacher,
        is_read=False
    ).order_by('-sent_at')[:5]
    
    context = {
        'teacher_classes': teacher_classes,
        'pending_attendance': pending_attendance,
        'assignments_to_mark': assignments_to_mark,
        'upcoming_exams': upcoming_exams,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'dashboards/teacher.html', context)


@role_required('office_admin', 'manager')
def office_admin_dashboard(request):
    """Office Administrator Dashboard"""
    today = date.today()
    
    # New registrations this week
    week_ago = today - timedelta(days=7)
    new_registrations = Student.objects.filter(
        admission_date__gte=week_ago
    ).order_by('-admission_date')
    
    # Pending invoices (not sent/printed)
    pending_invoices = FeeInvoice.objects.filter(
        status='pending'
    ).count()
    
    # Recent announcements
    recent_announcements = Announcement.objects.order_by('-created_at')[:5]
    
    # Upcoming fee deadlines
    upcoming_deadlines = FeeInvoice.objects.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=14),
        balance__gt=0
    ).values('due_date').annotate(
        count=Count('id'),
        total=Sum('balance')
    ).order_by('due_date')
    
    context = {
        'new_registrations': new_registrations,
        'pending_invoices': pending_invoices,
        'recent_announcements': recent_announcements,
        'upcoming_deadlines': upcoming_deadlines,
    }
    
    return render(request, 'dashboards/office_admin.html', context)


@bursar_or_manager
def bursar_dashboard(request):
    """Bursar / Accountant Dashboard"""
    today = date.today()
    
    # Today's collections
    today_collections = Payment.objects.filter(
        payment_date__date=today
    ).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # This week's collections
    week_ago = today - timedelta(days=7)
    week_collections = Payment.objects.filter(
        payment_date__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Balances owed by grade
    balances_by_grade = Student.objects.filter(
        status='active'
    ).values('current_class__grade__name').annotate(
        total_owed=Sum('fee_invoices__balance')
    ).order_by('current_class__grade__name')
    
    # Potential Earnings for Bursar
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(academic_year=current_year, is_current=True).first() if current_year else None
    potential_revenue = 0
    if current_year and current_term:
        active_students = Student.objects.filter(status='active')
        fee_map = {}
        for fee_structure in FeeStructure.objects.filter(academic_year=current_year).select_related('grade'):
            grade_id = getattr(fee_structure, 'grade_id', None) or getattr(getattr(fee_structure, 'grade', None), 'pk', None)
            if grade_id is not None:
                fee_map[grade_id] = fee_structure.amount
        for student in active_students:
            current_class = student.current_class
            grade_id = getattr(current_class, 'grade_id', None) or getattr(getattr(current_class, 'grade', None), 'pk', None)
            if grade_id is not None and grade_id in fee_map:
                potential_revenue += fee_map[grade_id]

    # Recent payments
    recent_payments = Payment.objects.select_related(
        'student', 'invoice', 'recorded_by'
    ).order_by('-payment_date')[:15]
    
    # Top debtors
    top_debtors = Student.objects.filter(
        status='active'
    ).annotate(
        total_debt=Sum('fee_invoices__balance')
    ).filter(total_debt__gt=0).order_by('-total_debt')[:10]
    
    context = {
        'today_total': today_collections['total'] or 0,
        'today_count': today_collections['count'] or 0,
        'week_total': week_collections,
        'balances_by_grade': balances_by_grade,
        'potential_revenue': potential_revenue,
        'recent_payments': recent_payments,
        'top_debtors': top_debtors,
    }
    
    return render(request, 'dashboards/bursar.html', context)


@role_required('auxiliary')
@auxiliary_required
def auxiliary_dashboard(request):
    """Auxiliary Staff Dashboard - Router based on assigned roles"""
    from .models import StaffRole
    
    # Get staff profile
    staff_profile = getattr(request.user, 'staff_profile', None)
    if not staff_profile:
        return render(request, 'dashboards/auxiliary_general.html')
    
    # Get assigned roles
    roles = staff_profile.roles.filter(is_active=True).values_list('role_type', flat=True)
    roles = list(roles)
    
    # Route to specialized dashboard based on primary role
    if 'cooking' in roles or 'cleaning_cooking' in roles:
        return cooking_staff_dashboard(request, roles)
    elif 'cleaning' in roles:
        return cleaning_staff_dashboard(request, roles)
    elif 'security' in roles:
        return security_staff_dashboard(request, roles)
    else:
        return render(request, 'dashboards/auxiliary_general.html')


@auxiliary_required
def cooking_staff_dashboard(request, roles=None):
    """Cooking Staff Dashboard - shows paid students, restocking, stock levels"""
    from finance.models import StudentLunchSubscription, RestockingRequest, StockItem
    from django.db.models import Count, Q
    
    if roles is None:
        roles = []
    
    today = date.today()
    staff_profile = request.user.staff_profile
    
    # Get all paid lunch subscribers (students with active subscriptions)
    paid_students = StudentLunchSubscription.objects.filter(
        status='active'
    ).select_related('student__user', 'student__current_class', 'plan').order_by('student__user__first_name')
    
    # Today's expected lunch students
    today_lunch = LunchAttendance.objects.filter(
        date=today,
        subscription__status='active'
    ).select_related('subscription__student__user', 'subscription__plan')
    
    # Stock levels (critical and low items)
    low_stock_items = StockItem.objects.filter(
        current_quantity__lte=F('minimum_threshold'),
        is_active=True
    ).order_by('current_quantity')
    
    critical_stock = StockItem.objects.filter(
        current_quantity=0,
        is_active=True
    )
    
    # Pending restocking requests (submitted by this staff)
    pending_requests = RestockingRequest.objects.filter(
        staff=staff_profile,
        status='pending'
    ).select_related('stock_item')
    
    # Approved requests
    approved_requests = RestockingRequest.objects.filter(
        staff=staff_profile,
        status='approved'
    ).select_related('stock_item')
    
    context = {
        'paid_students': paid_students,
        'paid_students_count': paid_students.count(),
        'today_lunch': today_lunch,
        'today_lunch_count': today_lunch.count(),
        'low_stock_items': low_stock_items,
        'critical_stock': critical_stock,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'has_cleaning_role': 'cleaning' in roles or 'cleaning_cooking' in roles,
        'has_cooking_role': 'cooking' in roles or 'cleaning_cooking' in roles,
    }
    
    return render(request, 'dashboards/cooking_staff.html', context)


@auxiliary_required
def cleaning_staff_dashboard(request, roles=None):
    """Cleaning Staff Dashboard"""
    if roles is None:
        roles = []
    
    context = {
        'has_cleaning_role': 'cleaning' in roles or 'cleaning_cooking' in roles,
        'has_cooking_role': 'cooking' in roles or 'cleaning_cooking' in roles,
    }
    return render(request, 'dashboards/cleaning_staff.html', context)


@auxiliary_required
def security_staff_dashboard(request, roles=None):
    """Security Staff Dashboard"""
    if roles is None:
        roles = []
    
    context = {
        'has_security_role': 'security' in roles,
    }
    return render(request, 'dashboards/security_staff.html', context)

    # Today's pickups (aggregate by route name)
    today_pickups = StudentTripAttendance.objects.filter(
        trip__trip_date=today
    ).values('trip__route__route_name').annotate(count=Count('id'))
    
    context = {
        'routes': routes,
        'today_pickups': today_pickups,
    }
    
    return render(request, 'dashboards/transport.html', context)


def cleaning_dashboard(request):
    """Cleaning Staff Dashboard"""
    # Duty roster, inspection checklists
    context = {}
    return render(request, 'dashboards/cleaning.html', context)


def _build_family_portal_context(members):
    """Build shared fee, attendance, and result data for parent/student portals."""
    family_members = list(members)

    if not family_members:
        return {
            'family_members': [],
            'fees_summary': [],
            'recent_results': [],
            'attendance_summary': [],
            'combined_total_invoiced': 0,
            'combined_total_paid': 0,
            'combined_total_outstanding': 0,
            'combined_attendance_total_days': 0,
            'combined_attendance_present': 0,
            'combined_attendance_rate': 0,
        }

    fees_summary = []
    for member in family_members:
        outstanding = FeeInvoice.objects.filter(
            student=member,
            balance__gt=0
        ).aggregate(total=Sum('balance'))['total'] or 0

        fees_summary.append({
            'student': member,
            'outstanding': outstanding,
        })

    combined_total_invoiced = FeeInvoice.objects.filter(
        student__in=family_members
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    combined_total_paid = FeeInvoice.objects.filter(
        student__in=family_members
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    combined_total_outstanding = FeeInvoice.objects.filter(
        student__in=family_members,
        balance__gt=0
    ).aggregate(total=Sum('balance'))['total'] or 0

    recent_results = ExamResult.objects.filter(
        student__in=family_members
    ).select_related('exam', 'student').order_by('-exam__exam_date')[:10]

    today = date.today()
    attendance_summary = []
    for member in family_members:
        total_days = StudentAttendance.objects.filter(
            student=member,
            date__month=today.month
        ).count()
        present = StudentAttendance.objects.filter(
            student=member,
            date__month=today.month,
            status='present'
        ).count()

        attendance_summary.append({
            'student': member,
            'total_days': total_days,
            'present': present,
            'rate': (present / total_days * 100) if total_days > 0 else 0,
        })

    combined_total_days = StudentAttendance.objects.filter(
        student__in=family_members,
        date__month=today.month
    ).count()
    combined_present = StudentAttendance.objects.filter(
        student__in=family_members,
        date__month=today.month,
        status='present'
    ).count()
    combined_attendance_rate = (combined_present / combined_total_days * 100) if combined_total_days > 0 else 0

    # Student-facing daily data surfaced for parents as a family view.
    try:
        Timetable = apps.get_model('academics', 'Timetable')
    except LookupError:
        Timetable = None

    todays_classes = []
    assignments_due = []
    weekday = today.strftime('%A').lower()

    for member in family_members:
        if not member.current_class:
            continue

        if Timetable:
            class_entries = Timetable.objects.filter(
                classroom=member.current_class,
                day_of_week=weekday,
                is_active=True,
            ).select_related('subject', 'teacher').order_by('start_time')

            for class_entry in class_entries:
                class_entry = cast(Any, class_entry)
                todays_classes.append({
                    'student': member,
                    'subject': class_entry.subject.name,
                    'teacher': class_entry.teacher.get_full_name() if class_entry.teacher else 'TBD',
                    'start_time': class_entry.start_time,
                    'end_time': class_entry.end_time,
                    'room': class_entry.room or 'N/A',
                })

        member_assignments = Assignment.objects.filter(
            classroom=member.current_class,
            due_date__gte=today,
        ).select_related('subject').order_by('due_date')[:5]

        for assignment in member_assignments:
            assignments_due.append({
                'student': member,
                'title': assignment.title,
                'subject': assignment.subject,
                'due_date': assignment.due_date,
            })

    return {
        'family_members': family_members,
        'fees_summary': fees_summary,
        'recent_results': recent_results,
        'attendance_summary': attendance_summary,
        'today': today,
        'todays_classes': todays_classes,
        'assignments_due': assignments_due,
        'combined_total_invoiced': combined_total_invoiced,
        'combined_total_paid': combined_total_paid,
        'combined_total_outstanding': combined_total_outstanding,
        'combined_attendance_total_days': combined_total_days,
        'combined_attendance_present': combined_present,
        'combined_attendance_rate': round(combined_attendance_rate, 1),
    }


@parent_access
def parent_dashboard(request):
    """Parent Portal Dashboard"""
    parent = request.user
    
    # Get parent's children
    children = Student.objects.filter(parent=parent)

    family_context = _build_family_portal_context(children)
    
    # Recent messages
    from communication.models import Message
    recent_messages = Message.objects.filter(
        recipient=parent,
        is_read=False
    ).order_by('-sent_at')[:5]
    
    context = {
        'children': children,
        'recent_messages': recent_messages,
    }
    context.update(family_context)
    
    return render(request, 'dashboards/parent.html', context)


@parent_access
def submit_edit_request(request):
    """Allow a parent to submit a generic edit request for a linked student."""
    from .notification_utils import send_approval_notification
    parent = request.user
    children = Student.objects.filter(parent=parent)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        field_name = request.POST.get('field_name')
        requested_value = request.POST.get('requested_value')

        try:
            student = Student.objects.get(pk=student_id, parent=parent)
        except Student.DoesNotExist:
            messages.error(request, 'Invalid student selected.')
            return redirect('frontend:dashboard')

        edit_request = EditRequest.objects.create(
            parent=parent,
            student=student,
            field_name=field_name,
            requested_value=requested_value,
        )
        
        from .services import ApprovalService
        ApprovalService.create_request(
            instance=edit_request,
            request_type='student_edit',
            reviewers=User.objects.filter(user_type__in=['admin', 'manager']),
            requested_by=parent,
            remarks=f'{field_name}: {requested_value}',
        )

        messages.success(request, 'Your edit request has been submitted and Admin/Manager will review it.')
        return redirect('frontend:dashboard')

    # allow preselecting a student via GET param
    selected = request.GET.get('student') or request.POST.get('student')
    return render(request, 'dashboards/request_edit.html', {'children': children, 'selected_student': selected})


@student_access
def student_dashboard(request):
    """Student Portal Dashboard"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        # No student record linked - show empty dashboard
        context = {
            'today': date.today(),
            'todays_classes': [],
            'assignments_due': [],
            'recent_results': [],
            'attendance': {'total_days': 0, 'present': 0, 'rate': 0},
        }
        return render(request, 'dashboards/student.html', context)
    
    today = date.today()
    family_context = _build_family_portal_context([student])
    
    # Today's classes (from timetable) - use runtime model lookup in case timetable model isn't present
    Timetable = apps.get_model('academics', 'Timetable')
    if Timetable:
        today_classes = Timetable.objects.filter(
            classroom=student.current_class,
            day_of_week=today.strftime('%A').lower()
        ).order_by('start_time')
    else:
        today_classes = []
    
    # Assignments due
    assignments_due = Assignment.objects.filter(
        classroom=student.current_class,
        due_date__gte=today
    ).order_by('due_date')[:5]
    
    # Recent results
    recent_results = ExamResult.objects.filter(
        student=student
    ).select_related('exam').order_by('-exam__exam_date')[:5]
    
    # Attendance summary (this month)
    total_days = StudentAttendance.objects.filter(
        student=student,
        date__month=today.month
    ).count()
    present = StudentAttendance.objects.filter(
        student=student,
        date__month=today.month,
        status='present'
    ).count()
    
    context = {
        'student': student,
        'today_classes': today_classes,
        'assignments_due': assignments_due,
        'recent_results': recent_results,
        'total_days': total_days,
        'present_days': present,
        'attendance_rate': (present / total_days * 100) if total_days > 0 else 0,
    }
    context.update(family_context)
    
    return render(request, 'dashboards/student.html', context)


# ============================================
# RESTOCKING & STOCK MANAGEMENT
# ============================================

def _teacher_stationery_items():
    from finance.models import StockItem

    stationery_seed_data = [
        {'name': 'Chalk', 'unit': 'boxes', 'current_quantity': 20, 'minimum_threshold': 5, 'unit_cost': 250, 'category': 'Stationery'},
        {'name': 'Whiteboard Marker', 'unit': 'units', 'current_quantity': 18, 'minimum_threshold': 6, 'unit_cost': 180, 'category': 'Stationery'},
        {'name': 'Exercise Book', 'unit': 'units', 'current_quantity': 120, 'minimum_threshold': 40, 'unit_cost': 120, 'category': 'Stationery'},
        {'name': 'Notebook', 'unit': 'units', 'current_quantity': 100, 'minimum_threshold': 30, 'unit_cost': 150, 'category': 'Stationery'},
        {'name': 'Pen', 'unit': 'boxes', 'current_quantity': 15, 'minimum_threshold': 5, 'unit_cost': 450, 'category': 'Stationery'},
        {'name': 'Pencil', 'unit': 'boxes', 'current_quantity': 15, 'minimum_threshold': 5, 'unit_cost': 400, 'category': 'Stationery'},
        {'name': 'Eraser', 'unit': 'boxes', 'current_quantity': 10, 'minimum_threshold': 3, 'unit_cost': 180, 'category': 'Stationery'},
        {'name': 'Ruler', 'unit': 'boxes', 'current_quantity': 8, 'minimum_threshold': 3, 'unit_cost': 300, 'category': 'Stationery'},
    ]

    if not StockItem.objects.filter(category__iexact='Stationery').exists():
        for item_data in stationery_seed_data:
            StockItem.objects.get_or_create(
                name=item_data['name'],
                category=item_data['category'],
                defaults=item_data,
            )

    return StockItem.objects.filter(category__iexact='Stationery', is_active=True).order_by('name')


@staff_only
def submit_restocking_request(request):
    """Allow staff to request supplies such as stationery or stock items."""
    from finance.models import StockItem, RestockingRequest
    from .services import ApprovalService
    
    staff_profile = getattr(request.user, 'staff_profile', None)
    if not staff_profile:
        messages.error(request, 'Your account is not linked to a staff profile.')
        return redirect('frontend:dashboard')
    
    is_teacher_request = request.user.user_type == 'teacher'

    if request.method == 'POST':
        stock_item_id = request.POST.get('stock_item')
        quantity = request.POST.get('quantity')
        reason = request.POST.get('reason')
        
        try:
            stock_item = StockItem.objects.get(pk=stock_item_id)
            quantity = float(quantity)
            
            # Create restocking request
            restocking_request = RestockingRequest.objects.create(
                staff=staff_profile,
                stock_item=stock_item,
                quantity_requested=quantity,
                reason=reason,
            )

            ApprovalService.create_request(
                instance=restocking_request,
                request_type='restock',
                reviewers=User.objects.filter(user_type__in=['admin', 'manager']),
                requested_by=staff_profile.user,
                remarks=reason,
            )
            
            messages.success(request, f'✓ Request for {stock_item.name} submitted. Manager/Admin have been notified.')
            return redirect('frontend:dashboard')
        except (StockItem.DoesNotExist, ValueError) as e:
            messages.error(request, f'Error submitting request: {str(e)}')
    
    # GET request: show form
    stock_items = _teacher_stationery_items() if is_teacher_request else StockItem.objects.filter(is_active=True).order_by('category', 'name')
    
    context = {
        'stock_items': stock_items,
        'is_teacher_request': is_teacher_request,
    }
    
    return render(request, 'dashboards/restocking_form.html', context)


@manager_required
def manager_approvals_dashboard(request):
    """Manager/Admin dashboard for approving restocking requests"""
    from finance.models import RestockingRequest

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        if action_type == 'mark_notification_read':
            notification_id = request.POST.get('notification_id')
            notification = Notification.objects.filter(pk=notification_id, recipient=request.user).first()
            if notification:
                notification.mark_as_read()
                messages.success(request, 'Notification marked as read.')
            else:
                messages.error(request, 'Notification not found.')
            return redirect(request.META.get('HTTP_REFERER') or 'frontend:manager_approvals')
    
    # Pending restocking requests
    pending_requests = RestockingRequest.objects.filter(
        status='pending'
    ).select_related('staff__user', 'stock_item').order_by('-created_at')
    
    # Recently approved
    approved_requests = RestockingRequest.objects.filter(
        status='approved'
    ).select_related('staff__user', 'stock_item').order_by('-reviewed_at')[:10]
    
    # Edit requests waiting approval
    pending_edits = EditRequest.objects.filter(
        status='pending'
    ).select_related('parent', 'student__user').order_by('-created_at')

    approval_requests = ApprovalRequest.objects.select_related(
        'content_type', 'requested_by', 'reviewed_by'
    ).prefetch_related('assigned_to').order_by('-created_at')
    pending_approval_requests = approval_requests.filter(status='pending')

    # Unified notification inbox for admin/manager approvals
    notifications = Notification.objects.filter(recipient=request.user)
    notification_search = request.GET.get('notification_search', '').strip()
    notification_type = request.GET.get('notification_type', '').strip()
    notification_status = request.GET.get('notification_status', 'unread').strip()

    if notification_search:
        notifications = notifications.filter(
            Q(title__icontains=notification_search) |
            Q(message__icontains=notification_search) |
            Q(content_type__icontains=notification_search)
        )

    if notification_type and notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)

    if notification_status and notification_status != 'all':
        notifications = notifications.filter(status=notification_status)

    notifications = notifications.order_by('-created_at')
    unread_notifications_count = Notification.objects.filter(recipient=request.user, status='unread').count()
    notifications_count = notifications.count()
    
    context = {
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests.count(),
        'approved_requests': approved_requests,
        'pending_edits': pending_edits,
        'pending_edits_count': pending_edits.count(),
        'approval_requests': approval_requests[:50],
        'pending_approval_requests_count': pending_approval_requests.count(),
        'notifications': notifications[:50],
        'notifications_count': notifications_count,
        'unread_notifications_count': unread_notifications_count,
        'notification_type_choices': Notification.NOTIFICATION_TYPES,
        'notification_search': notification_search,
        'notification_type_filter': notification_type,
        'notification_status_filter': notification_status,
        'pending_overall_count': pending_requests.count() + pending_edits.count() + pending_approval_requests.count() + unread_notifications_count,
    }
    
    return render(request, 'dashboards/manager_approvals.html', context)


@manager_required
def approve_approval_request(request, approval_id):
    """Approve a unified ApprovalRequest"""
    from .services import ApprovalService
    
    if request.method == 'POST':
        try:
            approval_request = ApprovalRequest.objects.get(pk=approval_id)
            remarks = request.POST.get('remarks', '')
            request_type_labels = dict(ApprovalRequest.REQUEST_TYPES)
            
            # Use ApprovalService to approve
            ApprovalService.approve(approval_request, request.user, remarks)
            
            messages.success(
                request, 
                f"Approved {request_type_labels.get(approval_request.request_type, approval_request.request_type)} request from {approval_request.requested_by.get_full_name()}"
            )
        except ApprovalRequest.DoesNotExist:
            messages.error(request, 'Approval request not found.')
        except Exception as e:
            messages.error(request, f'Error approving request: {str(e)}')
    
    return redirect('frontend:manager_approvals')


@manager_required
def reject_approval_request(request, approval_id):
    """Reject a unified ApprovalRequest"""
    from .services import ApprovalService
    
    if request.method == 'POST':
        try:
            approval_request = ApprovalRequest.objects.get(pk=approval_id)
            remarks = request.POST.get('remarks', '')
            request_type_labels = dict(ApprovalRequest.REQUEST_TYPES)
            
            if not remarks:
                messages.error(request, 'Please provide a reason for rejection.')
                return redirect('frontend:manager_approvals')
            
            # Use ApprovalService to reject
            ApprovalService.reject(approval_request, request.user, remarks)
            
            messages.success(
                request, 
                f"Rejected {request_type_labels.get(approval_request.request_type, approval_request.request_type)} request from {approval_request.requested_by.get_full_name()}"
            )
        except ApprovalRequest.DoesNotExist:
            messages.error(request, 'Approval request not found.')
        except Exception as e:
            messages.error(request, f'Error rejecting request: {str(e)}')
    
    return redirect('frontend:manager_approvals')


@manager_required
def approve_restocking_request(request, request_id):
    """Approve a restocking request"""
    from finance.models import RestockingRequest
    
    if request.method == 'POST':
        try:
            restocking_request = RestockingRequest.objects.get(pk=request_id)
            restocking_request.status = 'approved'
            restocking_request.reviewed_by = request.user
            restocking_request.reviewed_at = timezone.now()
            restocking_request.admin_notes = request.POST.get('admin_notes', '')
            restocking_request.save()
            
            messages.success(
                request, 
                f'Approved restocking request for {restocking_request.stock_item.name}'
            )
        except RestockingRequest.DoesNotExist:
            messages.error(request, 'Request not found.')
    
    return redirect('frontend:manager_approvals')


@manager_required
def reject_restocking_request(request, request_id):
    """Reject a restocking request"""
    from finance.models import RestockingRequest
    
    if request.method == 'POST':
        try:
            restocking_request = RestockingRequest.objects.get(pk=request_id)
            restocking_request.status = 'rejected'
            restocking_request.reviewed_by = request.user
            restocking_request.reviewed_at = timezone.now()
            restocking_request.admin_notes = request.POST.get('admin_notes', '')
            restocking_request.save()
            
            messages.success(
                request, 
                f'Rejected restocking request for {restocking_request.stock_item.name}'
            )
        except RestockingRequest.DoesNotExist:
            messages.error(request, 'Request not found.')
    
    return redirect('frontend:manager_approvals')


@manager_required
def manager_inventory_dashboard(request):
    """Manage requestable inventory items for teacher/staff requests."""
    from decimal import Decimal
    from django.shortcuts import get_object_or_404
    from finance.models import StockItem, StockTransaction

    def parse_decimal(value, default='0'):
        try:
            return Decimal(str(value if value not in [None, ''] else default))
        except Exception:
            return Decimal(default)

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'create_item':
            stock_item = StockItem.objects.create(
                name=request.POST.get('name', '').strip(),
                unit=request.POST.get('unit', 'units'),
                current_quantity=parse_decimal(request.POST.get('current_quantity')),
                minimum_threshold=parse_decimal(request.POST.get('minimum_threshold')),
                unit_cost=parse_decimal(request.POST.get('unit_cost')),
                category=request.POST.get('category', 'Stationery').strip() or 'Stationery',
                supplier=request.POST.get('supplier', '').strip(),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, f'Inventory item {stock_item.name} created.')
            return redirect('frontend:inventory_dashboard')

        if action_type == 'update_item':
            stock_item = get_object_or_404(StockItem, pk=request.POST.get('stock_item_id'))
            new_quantity = parse_decimal(request.POST.get('current_quantity'), stock_item.current_quantity)
            quantity_delta = new_quantity - stock_item.current_quantity

            stock_item.name = request.POST.get('name', stock_item.name).strip()
            stock_item.unit = request.POST.get('unit', stock_item.unit)
            stock_item.minimum_threshold = parse_decimal(request.POST.get('minimum_threshold'), stock_item.minimum_threshold)
            stock_item.unit_cost = parse_decimal(request.POST.get('unit_cost'), str(stock_item.unit_cost))
            stock_item.category = request.POST.get('category', stock_item.category).strip() or stock_item.category
            stock_item.supplier = request.POST.get('supplier', stock_item.supplier).strip()
            stock_item.is_active = request.POST.get('is_active') == 'on'
            stock_item.save()

            if quantity_delta != 0:
                StockTransaction.objects.create(
                    stock_item=stock_item,
                    transaction_type='purchase' if quantity_delta > 0 else 'usage',
                    quantity=abs(quantity_delta),
                    recorded_by=request.user,
                    notes='Manual inventory adjustment from manager inventory page',
                )

            messages.success(request, f'Inventory item {stock_item.name} updated.')
            return redirect('frontend:inventory_dashboard')

        if action_type == 'adjust_stock':
            stock_item = get_object_or_404(StockItem, pk=request.POST.get('stock_item_id'))
            transaction_type = request.POST.get('transaction_type', 'adjustment')
            quantity = parse_decimal(request.POST.get('quantity'))

            if quantity > 0:
                if transaction_type == 'usage':
                    tx_type = 'usage'
                elif transaction_type == 'damage':
                    tx_type = 'damage'
                elif transaction_type == 'transfer':
                    tx_type = 'transfer'
                else:
                    tx_type = 'purchase'

                StockTransaction.objects.create(
                    stock_item=stock_item,
                    transaction_type=tx_type,
                    quantity=quantity,
                    recorded_by=request.user,
                    notes=request.POST.get('notes', '').strip(),
                )

                messages.success(request, f'{stock_item.name} stock updated.')
            else:
                messages.error(request, 'Quantity must be greater than zero.')

            return redirect('frontend:inventory_dashboard')

    search = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()

    stock_items = StockItem.objects.all().order_by('category', 'name')
    if search:
        stock_items = stock_items.filter(Q(name__icontains=search) | Q(category__icontains=search) | Q(supplier__icontains=search))
    if category_filter:
        stock_items = stock_items.filter(category__iexact=category_filter)

    categories = StockItem.objects.values_list('category', flat=True).distinct().order_by('category')
    recent_transactions = StockTransaction.objects.select_related('stock_item', 'recorded_by').order_by('-transaction_date', '-created_at')[:12]
    summary = {
        'total_items': stock_items.count(),
        'low_stock_items': stock_items.filter(current_quantity__lte=F('minimum_threshold')).count(),
        'stationery_items': StockItem.objects.filter(category__iexact='Stationery', is_active=True).count(),
    }

    context = {
        'stock_items': stock_items,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
        'recent_transactions': recent_transactions,
        'summary': summary,
        'unit_choices': StockItem.UNIT_CHOICES,
        'transaction_types': StockTransaction.TRANSACTION_TYPE_CHOICES,
    }
    return render(request, 'dashboards/inventory_dashboard.html', context)
