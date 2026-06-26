from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta, date
from administration.models import Student, Staff, ClassRoom, AcademicYear, Term
from finance.models import FeeInvoice, Payment
from attendance.models import StudentAttendance
from academics.models import ExamResult
from administration.decorators import manager_required


@manager_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    today = date.today()
    current_month = today.replace(day=1)
    
    # Student Analytics
    total_students = Student.objects.filter(status='enrolled').count()
    students_by_grade = Student.objects.filter(status='enrolled').values(
        'current_class__grade__name'
    ).annotate(count=Count('id')).order_by('current_class__grade__name')
    
    # Staff Analytics
    total_staff = Staff.objects.filter(is_active=True).count()
    staff_by_department = Staff.objects.filter(is_active=True).values(
        'department'
    ).annotate(count=Count('id')).order_by('department')
    
    # Financial Analytics - Current Month
    month_invoices = FeeInvoice.objects.filter(
        issue_date__gte=current_month,
        issue_date__lt=current_month + timedelta(days=32)
    )
    
    total_expected = month_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_collected = month_invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_pending = month_invoices.aggregate(Sum('balance'))['balance__sum'] or 0
    
    collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
    
    # Attendance Analytics - Last 30 days
    thirty_days_ago = today - timedelta(days=30)
    attendance_stats = StudentAttendance.objects.filter(
        date__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late'))
    )
    
    attendance_rate = (attendance_stats['present'] / attendance_stats['total'] * 100) if attendance_stats['total'] > 0 else 0
    
    # Academic Performance - Current Term
    current_term = Term.objects.filter(is_current=True).first()
    if current_term:
        term_results = ExamResult.objects.filter(
            exam__term=current_term
        ).aggregate(
            avg_score=Avg('score'),
            total_exams=Count('id')
        )
    else:
        term_results = {'avg_score': 0, 'total_exams': 0}
    
    # Trend Data for Charts - Last 6 months
    six_months_ago = current_month - timedelta(days=180)
    monthly_collections = []
    monthly_attendance = []
    
    for i in range(6):
        month_date = current_month - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        # Collection for this month
        month_payments = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_collections.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_payments)
        })
        
        # Attendance for this month
        month_attendance = StudentAttendance.objects.filter(
            date__gte=month_start,
            date__lt=month_end
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present'))
        )
        
        rate = (month_attendance['present'] / month_attendance['total'] * 100) if month_attendance['total'] > 0 else 0
        monthly_attendance.append({
            'month': month_start.strftime('%b %Y'),
            'rate': round(rate, 1)
        })
    
    monthly_collections.reverse()
    monthly_attendance.reverse()
    
    context = {
        # Summary Stats
        'total_students': total_students,
        'total_staff': total_staff,
        'collection_rate': round(collection_rate, 1),
        'attendance_rate': round(attendance_rate, 1),
        
        # Financial
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_pending': total_pending,
        
        # Attendance
        'attendance_stats': attendance_stats,
        
        # Academic
        'term_results': term_results,
        'current_term': current_term,
        
        # Distribution
        'students_by_grade': list(students_by_grade),
        'staff_by_department': list(staff_by_department),
        
        # Trends
        'monthly_collections': monthly_collections,
        'monthly_attendance': monthly_attendance,
    }
    
    return render(request, 'frontend/analytics/dashboard.html', context)


@manager_required
def student_performance_analytics(request):
    """Detailed student performance analytics"""
    # Get current term
    current_term = Term.objects.filter(is_current=True).first()
    
    if not current_term:
        context = {'error': 'No active term found'}
        return render(request, 'frontend/analytics/performance.html', context)
    
    # Overall performance
    all_results = ExamResult.objects.filter(exam__term=current_term)
    
    performance_summary = {
        'total_exams': all_results.count(),
        'average_score': all_results.aggregate(Avg('score'))['score__avg'] or 0,
        'highest_score': all_results.aggregate(Max('score'))['score__max'] or 0,
        'lowest_score': all_results.aggregate(Min('score'))['score__min'] or 0,
    }
    
    # Grade distribution
    grade_distribution = all_results.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')
    
    # Top performers
    top_students = ExamResult.objects.filter(
        exam__term=current_term
    ).values(
        'student__first_name', 'student__last_name', 'student_id'
    ).annotate(
        avg_score=Avg('score'),
        total_exams=Count('id')
    ).order_by('-avg_score')[:10]
    
    # Performance by class
    class_performance = ExamResult.objects.filter(
        exam__term=current_term
    ).values(
        'student__current_class__grade__name',
        'student__current_class__section'
    ).annotate(
        avg_score=Avg('score'),
        total_students=Count('student_id', distinct=True)
    ).order_by('-avg_score')
    
    context = {
        'current_term': current_term,
        'performance_summary': performance_summary,
        'grade_distribution': list(grade_distribution),
        'top_students': list(top_students),
        'class_performance': list(class_performance),
    }
    
    return render(request, 'frontend/analytics/performance.html', context)


@manager_required
def financial_analytics(request):
    """Detailed financial analytics"""
    today = date.today()
    current_month = today.replace(day=1)
    
    # Year-to-date summary
    year_start = today.replace(month=1, day=1)
    ytd_invoices = FeeInvoice.objects.filter(issue_date__gte=year_start)
    ytd_payments = Payment.objects.filter(payment_date__gte=year_start)
    
    ytd_summary = {
        'total_invoiced': ytd_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'total_collected': ytd_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_pending': ytd_invoices.aggregate(Sum('balance'))['balance__sum'] or 0,
    }
    
    # Monthly breakdown - Last 12 months
    monthly_data = []
    for i in range(12):
        month_date = current_month - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_invoiced = FeeInvoice.objects.filter(
            issue_date__gte=month_start,
            issue_date__lt=month_end
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        month_collected = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lt=month_end
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'invoiced': float(month_invoiced),
            'collected': float(month_collected),
        })
    
    monthly_data.reverse()
    
    # Payment methods breakdown
    payment_methods = Payment.objects.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Top defaulters
    defaulters = Student.objects.filter(
        status='enrolled'
    ).annotate(
        total_balance=Sum('fee_invoices__balance')
    ).filter(total_balance__gt=0).order_by('-total_balance')[:10]
    
    context = {
        'ytd_summary': ytd_summary,
        'monthly_data': monthly_data,
        'payment_methods': list(payment_methods),
        'defaulters': defaulters,
    }
    
    return render(request, 'frontend/analytics/financial.html', context)
