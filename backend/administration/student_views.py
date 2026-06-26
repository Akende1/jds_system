"""
Student management views for frontend
"""
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponseForbidden
from django.utils import timezone
from .decorators import teacher_or_above, head_teacher_or_manager, staff_only
from .models import Student, ClassRoom, Grade, AcademicYear
from .models_class_management import StudentSuspension, StudentExpulsion
from finance.models import FeeInvoice
from attendance.models import StudentAttendance
from administration.permissions import UserHierarchy
from .utils.excel_exporter import export_students_to_excel
from datetime import date


@teacher_or_above
def student_list(request):
    """Student listing with filters and search"""
    students = Student.objects.select_related(
        'current_class', 'current_class__grade'
    ).filter(status='active')

    if request.user.user_type == 'teacher':
        students = students.filter(
            Q(current_class__teacher_assignments__teacher=request.user, current_class__teacher_assignments__is_active=True) |
            Q(current_class__class_teacher=request.user)
        ).distinct()
    
    # Filters
    search = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    class_filter = request.GET.get('class', '')
    gender_filter = request.GET.get('gender', '')
    
    if search:
        students = students.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(admission_number__icontains=search)
        )
    
    if grade_filter:
        students = students.filter(current_class__grade_id=grade_filter)
    
    if class_filter:
        students = students.filter(current_class_id=class_filter)
    
    if gender_filter:
        students = students.filter(gender=gender_filter)
    
    # Pagination
    paginator = Paginator(students, 50)
    page = request.GET.get('page', 1)
    students_page = paginator.get_page(page)
    
    # Get filter options
    grades = Grade.objects.all()
    classes = ClassRoom.objects.select_related('grade').all()
    if request.user.user_type == 'teacher':
        classes = UserHierarchy.get_accessible_classes(request.user).select_related('grade')
    
    context = {
        'students': students_page,
        'grades': grades,
        'classes': classes,
        'search': search,
        'grade_filter': grade_filter,
        'class_filter': class_filter,
        'gender_filter': gender_filter,
        'total_count': students.count(),
    }
    
    return render(request, 'frontend/students/list.html', context)


@head_teacher_or_manager
def student_export(request):
    """Export all students for leader roles."""
    students = Student.objects.select_related('user', 'current_class', 'current_class__grade').filter(status='active')
    if request.GET.get('grade'):
        students = students.filter(current_class__grade_id=request.GET.get('grade'))
    if request.GET.get('class'):
        students = students.filter(current_class_id=request.GET.get('class'))

    export_path = export_students_to_excel(students)
    return FileResponse(
        open(export_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(export_path),
    )


@staff_only
def student_detail(request, pk):
    """Student detail page with complete profile"""
    student = get_object_or_404(
        Student.objects.select_related(
            'current_class', 'current_class__grade', 'parent'
        ),
        pk=pk
    )

    if request.user.user_type == 'teacher' and not UserHierarchy.get_accessible_students(request.user).filter(pk=student.pk).exists():
        messages.error(request, 'You can only view students in your assigned classes.')
        return redirect('frontend:student_list')
    
    can_view_financials = request.user.is_superuser or request.user.user_type in {'admin', 'manager', 'head_teacher'}
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Financial summary is restricted to school leaders, not teachers.
    if can_view_financials:
        invoices = FeeInvoice.objects.filter(
            student=student,
            academic_year=current_year
        )
        total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_paid = invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        balance = total_invoiced - total_paid
        financial_summary = {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'balance': balance,
        }
    else:
        financial_summary = {
            'total_invoiced': 0,
            'total_paid': 0,
            'balance': 0,
        }
    
    # Attendance summary (current term)
    total_days = StudentAttendance.objects.filter(
        student=student,
        date__month=date.today().month
    ).count()
    present_days = StudentAttendance.objects.filter(
        student=student,
        date__month=date.today().month,
        status='present'
    ).count()
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Recent exam results
    from academics.models import ExamResult
    recent_results = ExamResult.objects.filter(
        student=student
    ).select_related('exam', 'exam__subject').order_by('-exam__exam_date')[:10]
    
    # Recent payments are also leader-only.
    if can_view_financials:
        from finance.models import Payment
        recent_payments = Payment.objects.filter(
            student=student
        ).order_by('-payment_date')[:5]
    else:
        recent_payments = []
    
    context = {
        'student': student,
        'can_view_financials': can_view_financials,
        'financial_summary': financial_summary,
        'total_days': total_days,
        'present_days': present_days,
        'attendance_rate': attendance_rate,
        'recent_results': recent_results,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'frontend/students/detail.html', context)


@head_teacher_or_manager
def student_register(request):
    """Register new student"""
    if request.method == 'POST':
        # Extract form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        current_class_id = request.POST.get('current_class')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        # Parent info
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        parent_email = request.POST.get('parent_email')
        
        try:
            # Generate admission number
            last_student = Student.objects.order_by('-admission_number').first()
            if last_student and last_student.admission_number:
                last_num = int(last_student.admission_number.split('-')[1])
                admission_number = f"STD-{str(last_num + 1).zfill(5)}"
            else:
                admission_number = "STD-00001"
            
            # Create a user record for the student, then the Student profile
            from .models import User
            username = admission_number
            student_user = User.objects.create_user(
                username=username,
                email=email or f"{username}@example.com",
                first_name=first_name or '',
                last_name=last_name or '',
                user_type='student'
            )

            student = Student.objects.create(
                user=student_user,
                admission_number=admission_number,
                current_class_id=current_class_id,
                gender=gender or '',
                guardian_name=parent_name or '',
                guardian_phone=parent_phone or '',
                guardian_email=parent_email or '',
                guardian_address=address or '',
                admission_date=date.today(),
                status='active'
            )
            
            # Create parent user if provided
            if parent_name and parent_email:
                from .models import User
                parent_user = User.objects.create_user(
                    username=parent_email,
                    email=parent_email,
                    first_name=parent_name.split()[0],
                    last_name=' '.join(parent_name.split()[1:]) if len(parent_name.split()) > 1 else '',
                    user_type='parent',
                    phone_number=parent_phone
                )
                setattr(student, 'parent', parent_user)
                student.save()
            
            messages.success(request, f'Student {student.user.get_full_name()} registered successfully!')
            return redirect('frontend:student_detail', pk=student.pk)
        
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')
    
    # GET request
    grades = Grade.objects.all()
    classes = ClassRoom.objects.select_related('grade').all()
    
    context = {
        'grades': grades,
        'classes': classes,
    }
    
    return render(request, 'frontend/students/register.html', context)


@head_teacher_or_manager
def student_edit(request, pk):
    """Edit student information"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        # Update user and student fields
        student.user.first_name = request.POST.get('first_name', student.user.first_name)
        student.user.last_name = request.POST.get('last_name', student.user.last_name)
        # User has date_of_birth and contact fields
        student.user.date_of_birth = request.POST.get('date_of_birth', student.user.date_of_birth)
        student.user.phone_number = request.POST.get('phone_number', student.user.phone_number)
        student.user.email = request.POST.get('email', student.user.email)
        student.user.save()

        student.gender = request.POST.get('gender', student.gender)
        current_class_id = request.POST.get('current_class', getattr(student, 'current_class_id', None))
        setattr(student, 'current_class_id', current_class_id)
        student.guardian_name = request.POST.get('guardian_name', student.guardian_name)
        student.guardian_phone = request.POST.get('guardian_phone', student.guardian_phone)
        student.guardian_email = request.POST.get('guardian_email', student.guardian_email)
        student.guardian_address = request.POST.get('guardian_address', student.guardian_address)
        student.save()
        
        messages.success(request, 'Student information updated successfully!')
        return redirect('frontend:student_detail', pk=student.pk)
    
    # GET request
    grades = Grade.objects.all()
    classes = ClassRoom.objects.select_related('grade').all()
    
    context = {
        'student': student,
        'grades': grades,
        'classes': classes,
    }
    
    return render(request, 'frontend/students/edit.html', context)


@head_teacher_or_manager
def student_promote(request):
    """Bulk student promotion"""
    if request.method == 'POST':
        # Get selected students or filters
        student_ids = request.POST.getlist('students')
        from_class_id = request.POST.get('from_class')
        to_class_id = request.POST.get('to_class')
        
        if not to_class_id:
            messages.error(request, 'Please select a destination class')
            return redirect('frontend:student_promote')
        
        try:
            # Get students to promote
            if student_ids:
                students = Student.objects.filter(id__in=student_ids)
            elif from_class_id:
                students = Student.objects.filter(current_class_id=from_class_id)
            else:
                messages.error(request, 'Please select students or a class')
                return redirect('frontend:student_promote')
            
            # Promote students
            promoted_count = students.update(current_class_id=to_class_id)
            
            # Create promotion records
            from .models_class_management import ClassPromotion
            to_class = ClassRoom.objects.get(id=to_class_id)
            current_year = AcademicYear.objects.filter(is_current=True).first()
            
            for student in students:
                ClassPromotion.objects.create(
                    student=student,
                    from_class_id=from_class_id if from_class_id else getattr(student, 'current_class_id', None),
                    to_class=to_class,
                    academic_year=current_year,
                    status='approved',
                    approved_by=request.user,
                    approved_date=date.today()
                )
            
            messages.success(request, f'{promoted_count} students promoted successfully!')
            return redirect('frontend:student_list')
        
        except Exception as e:
            messages.error(request, f'Error promoting students: {str(e)}')
    
    # GET request
    classes = ClassRoom.objects.select_related('grade').all()
    
    context = {
        'classes': classes,
    }
    
    return render(request, 'frontend/students/promote.html', context)


@teacher_or_above
def student_transfer(request):
    """Transfer student between classes"""
    if request.method == 'POST':
        student_id = request.POST.get('student')
        to_class_id = request.POST.get('to_class')
        reason = request.POST.get('reason')
        
        try:
            student = Student.objects.get(id=student_id)
            if request.user.user_type == 'teacher' and not UserHierarchy.get_accessible_students(request.user).filter(pk=student.pk).exists():
                messages.error(request, 'You can only request transfers for students in your assigned classes.')
                return redirect('frontend:student_transfer')

            from_class = student.current_class
            to_class = ClassRoom.objects.get(id=to_class_id)
            
            # Create transfer record
            from .models_class_management import StudentTransfer
            transfer = StudentTransfer.objects.create(
                student=student,
                from_class=from_class,
                to_class=to_class,
                transfer_type='request' if request.user.user_type == 'teacher' else 'section',
                reason=reason,
                requested_by=request.user,
                status='requested' if request.user.user_type == 'teacher' else 'approved',
                approved_by=None if request.user.user_type == 'teacher' else request.user,
                approved_date=None if request.user.user_type == 'teacher' else date.today()
            )
            
            if request.user.user_type != 'teacher':
                # Update student class immediately for management users
                student.current_class = to_class
                student.save()
            
            if request.user.user_type == 'teacher':
                messages.success(request, f'Transfer request submitted for {student.user.get_full_name()}.')
            else:
                messages.success(request, f'{student.user.get_full_name()} transferred successfully!')
            return redirect('frontend:student_detail', pk=student.pk)
        
        except Exception as e:
            messages.error(request, f'Error transferring student: {str(e)}')
    
    # GET request
    students = Student.objects.filter(status='active').select_related('current_class')
    classes = ClassRoom.objects.select_related('grade').all()

    if request.user.user_type == 'teacher':
        students = UserHierarchy.get_accessible_students(request.user).select_related('current_class')
        classes = UserHierarchy.get_accessible_classes(request.user).select_related('grade')
    
    context = {
        'students': students,
        'classes': classes,
    }
    
    return render(request, 'frontend/students/transfer.html', context)


# ============================================
# STUDENT DISCIPLINARY ACTIONS
# ============================================

@head_teacher_or_manager
def student_suspension_list(request):
    """List all student suspensions"""
    suspensions = StudentSuspension.objects.select_related('student__user', 'requested_by', 'approved_by').all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        suspensions = suspensions.filter(status=status_filter)
    
    context = {
        'suspensions': suspensions,
        'status_filter': status_filter,
        'statuses': StudentSuspension.STATUS_CHOICES,
    }
    
    return render(request, 'frontend/students/suspension_list.html', context)


@head_teacher_or_manager
def student_suspension_request(request, pk):
    """Request suspension for a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        from datetime import datetime
        start_date = request.POST.get('suspension_start_date')
        end_date = request.POST.get('suspension_end_date')
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        duration = (end - start).days
        
        suspension = StudentSuspension.objects.create(
            student=student,
            requested_by=request.user,
            reason=request.POST.get('reason'),
            detailed_reason=request.POST.get('detailed_reason'),
            suspension_start_date=start,
            suspension_end_date=end,
            duration_days=duration,
        )
        messages.success(request, f'Suspension request created for {student.full_name}')
        return redirect('frontend:student_detail', pk=pk)
    
    context = {
        'student': student,
        'reasons': StudentSuspension.REASON_CHOICES,
    }
    
    return render(request, 'frontend/students/suspension_request.html', context)


@head_teacher_or_manager
def student_suspension_detail(request, pk):
    """View and manage student suspension"""
    suspension = get_object_or_404(StudentSuspension, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            suspension.status = 'approved'
            suspension.approved_by = request.user
            suspension.approval_date = timezone.now().date()
            suspension.approval_notes = request.POST.get('approval_notes', '')
            suspension.save()
            messages.success(request, 'Suspension approved')
        elif action == 'reject':
            suspension.status = 'rejected'
            suspension.approved_by = request.user
            suspension.approval_date = timezone.now().date()
            suspension.approval_notes = request.POST.get('approval_notes', '')
            suspension.save()
            messages.error(request, 'Suspension rejected')
        elif action == 'notify_parent':
            suspension.parent_notified = True
            suspension.parent_notification_date = timezone.now().date()
            suspension.save()
            messages.success(request, 'Parent notified of suspension')
        
        return redirect('frontend:student_suspension_detail', pk=pk)
    
    context = {
        'suspension': suspension,
    }
    
    return render(request, 'frontend/students/suspension_detail.html', context)


@head_teacher_or_manager
def student_expulsion_list(request):
    """List all student expulsions"""
    expulsions = StudentExpulsion.objects.select_related(
        'student__user', 'recommended_by', 'reviewed_by', 'approved_by'
    ).all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        expulsions = expulsions.filter(status=status_filter)
    
    context = {
        'expulsions': expulsions,
        'status_filter': status_filter,
        'statuses': StudentExpulsion.STATUS_CHOICES,
    }
    
    return render(request, 'frontend/students/expulsion_list.html', context)


@head_teacher_or_manager
def student_expulsion_recommend(request, pk):
    """Recommend expulsion for a student"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        from datetime import datetime
        incident_date = request.POST.get('incident_date')
        
        expulsion = StudentExpulsion.objects.create(
            student=student,
            recommended_by=request.user,
            reason=request.POST.get('reason'),
            detailed_reason=request.POST.get('detailed_reason'),
            incident_date=datetime.strptime(incident_date, '%Y-%m-%d').date(),
            investigation_notes=request.POST.get('investigation_notes', ''),
            witnesses=request.POST.get('witnesses', ''),
            evidence=request.POST.get('evidence', ''),
        )
        messages.success(request, f'Expulsion recommended for {student.full_name}')
        return redirect('frontend:student_detail', pk=pk)
    
    context = {
        'student': student,
        'reasons': StudentExpulsion.REASON_CHOICES,
    }
    
    return render(request, 'frontend/students/expulsion_recommend.html', context)


@head_teacher_or_manager
def student_expulsion_detail(request, pk):
    """View and manage student expulsion"""
    expulsion = get_object_or_404(StudentExpulsion, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'review':
            expulsion.status = 'under_review'
            expulsion.reviewed_by = request.user
            expulsion.review_date = timezone.now().date()
            expulsion.review_notes = request.POST.get('review_notes', '')
            expulsion.investigation_completed = True
            expulsion.save()
            messages.success(request, 'Expulsion moved to under review')
        elif action == 'approve':
            expulsion.status = 'approved'
            expulsion.approved_by = request.user
            expulsion.approval_date = timezone.now().date()
            expulsion.approval_notes = request.POST.get('approval_notes', '')
            expulsion.save()
            messages.success(request, 'Expulsion approved')
        elif action == 'reject':
            expulsion.status = 'rejected'
            expulsion.approved_by = request.user
            expulsion.approval_date = timezone.now().date()
            expulsion.approval_notes = request.POST.get('approval_notes', '')
            expulsion.save()
            messages.error(request, 'Expulsion rejected')
        elif action == 'execute':
            expulsion.status = 'executed'
            expulsion.expulsion_effective_date = timezone.now().date()
            expulsion.final_record_note = request.POST.get('final_record_note', '')
            # Update student status
            expulsion.student.status = 'expelled'
            expulsion.student.is_active = False
            expulsion.student.save()
            expulsion.save()
            messages.success(request, f'{expulsion.student.full_name} has been expelled')
        elif action == 'notify_parent':
            expulsion.parent_meeting_held = True
            expulsion.parent_meeting_date = timezone.now().date()
            expulsion.parent_meeting_notes = request.POST.get('parent_meeting_notes', '')
            expulsion.parent_notified = True
            expulsion.parent_notification_date = timezone.now().date()
            expulsion.save()
            messages.success(request, 'Parent meeting recorded and notified')
        
        return redirect('frontend:student_expulsion_detail', pk=pk)
    
    context = {
        'expulsion': expulsion,
    }
    
    return render(request, 'frontend/students/expulsion_detail.html', context)
