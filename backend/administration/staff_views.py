import secrets

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from administration.models import Staff, User, ClassRoom
from administration.decorators import manager_required, staff_only
from hr.models import LeaveApplication, StaffDisciplinaryAction, StaffSuspensionRequest, StaffTerminationRequest


def _generate_onboarding_token():
    token = secrets.token_urlsafe(32)
    while User.objects.filter(onboarding_token=token).exists():
        token = secrets.token_urlsafe(32)
    return token


def _send_staff_onboarding_email(request, user):
    if not user.email:
        return None

    onboarding_url = request.build_absolute_uri(
        reverse('frontend:staff_onboarding_complete', kwargs={'token': user.onboarding_token})
    )
    subject = 'Complete your staff profile'
    message = (
        f"Hello {user.first_name or user.get_full_name() or user.username},\n\n"
        f"Your staff account has been created. Complete your profile and set your password using this link:\n"
        f"{onboarding_url}\n\n"
        "You will use this account to log in after completion."
    )

    send_mail(
        subject,
        message,
        getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        [user.email],
        fail_silently=True,
    )
    return onboarding_url


def _build_staff_profile_context(staff_member, require_password=False):
    return {
        'staff': staff_member,
        'require_password': require_password,
        'staff_types': Staff.STAFF_TYPE_CHOICES,
        'employment_types': Staff.EMPLOYMENT_TYPE_CHOICES,
        'genders': [('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
    }


def _finalize_staff_profile(request, staff_member, user, require_password=False):
    user.first_name = request.POST.get('first_name', user.first_name)
    user.last_name = request.POST.get('last_name', user.last_name)
    user.email = request.POST.get('email', user.email)
    user.phone_number = request.POST.get('phone_number', user.phone_number)
    user.address = request.POST.get('address', user.address)
    date_of_birth = request.POST.get('date_of_birth')
    if date_of_birth:
        user.date_of_birth = date_of_birth

    password = request.POST.get('password', '')
    confirm_password = request.POST.get('confirm_password', '')
    if require_password:
        if not password or password != confirm_password:
            raise ValueError('Password and confirmation must match.')
        user.set_password(password)
    elif password:
        if password != confirm_password:
            raise ValueError('Password and confirmation must match.')
        user.set_password(password)

    user.onboarding_completed = True
    user.onboarding_token = None
    user.onboarding_token_created_at = None
    user.is_active = True
    user.save()

    staff_member.tpin_no = request.POST.get('tpin_no', staff_member.tpin_no)
    staff_member.nrc_no = request.POST.get('nrc_no', staff_member.nrc_no)
    staff_member.gender = request.POST.get('gender', staff_member.gender)
    staff_member.designation = request.POST.get('designation', staff_member.designation)
    staff_member.department = request.POST.get('department', staff_member.department)
    staff_member.date_of_joining = request.POST.get('date_of_joining', staff_member.date_of_joining)
    staff_member.qualification = request.POST.get('qualification', staff_member.qualification)
    staff_member.experience_years = request.POST.get('experience_years', staff_member.experience_years or 0)
    staff_member.employment_type = request.POST.get('employment_type', staff_member.employment_type)
    staff_member.staff_type = request.POST.get('staff_type', staff_member.staff_type)
    staff_member.bank_name = request.POST.get('bank_name', staff_member.bank_name)
    staff_member.account_number = request.POST.get('account_number', staff_member.account_number)
    staff_member.marital_status = request.POST.get('marital_status', staff_member.marital_status)

    if request.FILES.get('nrc_front'):
        staff_member.nrc_front = request.FILES['nrc_front']
    if request.FILES.get('nrc_back'):
        staff_member.nrc_back = request.FILES['nrc_back']
    if request.FILES.get('other_documents'):
        staff_member.other_documents = request.FILES['other_documents']

    staff_member.profile_completed_at = timezone.now()
    staff_member.is_active = True
    staff_member.save()


def _lookup_staff_for_completion(token=None, pk=None):
    if token:
        user = get_object_or_404(User, onboarding_token=token)
        return get_object_or_404(Staff.objects.select_related('user'), user=user), user

    staff_member = get_object_or_404(Staff.objects.select_related('user'), pk=pk)
    return staff_member, staff_member.user


@staff_only
def staff_list(request):
    """List all staff members"""
    staff = Staff.objects.select_related('user').filter(is_active=True)
    incomplete_staff = staff.filter(user__onboarding_completed=False)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        staff = staff.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(staff_id__icontains=search) |
            Q(department__icontains=search)
        )
    
    # Filter by department
    department = request.GET.get('department', '')
    if department:
        staff = staff.filter(department=department)
    
    # Get all departments for filter
    departments = Staff.objects.values_list('department', flat=True).distinct()
    
    context = {
        'staff': staff,
        'incomplete_staff': incomplete_staff,
        'search': search,
        'department': department,
        'departments': departments,
    }
    
    return render(request, 'frontend/staff/list.html', context)


@staff_only
def staff_detail(request, pk):
    """View staff member details with payslip info"""
    staff_member = get_object_or_404(Staff.objects.select_related('user'), pk=pk)
    
    # Get assigned classes
    assigned_classes = ClassRoom.objects.filter(
        Q(class_teacher=staff_member.user) | Q(teacher_assignments__teacher=staff_member.user)
    ).distinct().select_related('grade')
    
    # Get recent leave applications
    recent_leaves = LeaveApplication.objects.filter(
        staff=staff_member
    ).select_related('leave_type').order_by('-applied_on')[:5]
    
    # Get recent payslips (if manager/admin viewing)
    recent_payslips = None
    active_allowances = None
    active_deductions = None
    
    if request.user.user_type in ['admin', 'manager'] or request.user == staff_member.user:
        from hr.models import PaySlip, StaffAllowance, StaffDeduction
        
        recent_payslips = PaySlip.objects.filter(
            staff=staff_member
        ).order_by('-payslip_period_end')[:6]
        
        active_allowances = StaffAllowance.objects.filter(
            staff=staff_member,
            status='active'
        ).order_by('-start_date')
        
        active_deductions = StaffDeduction.objects.filter(
            staff=staff_member,
            status='active'
        ).order_by('-start_date')
    
    context = {
        'staff': staff_member,
        'assigned_classes': assigned_classes,
        'recent_leaves': recent_leaves,
        'recent_payslips': recent_payslips,
        'active_allowances': active_allowances,
        'active_deductions': active_deductions,
        'profile_incomplete': not staff_member.user.onboarding_completed,
    }
    
    return render(request, 'frontend/staff/detail.html', context)


@manager_required
def staff_add(request):
    """Add new staff member"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        user_type = request.POST.get('user_type', 'teacher')
        if not email:
            messages.error(request, 'Email is required to create a staff account.')
            return redirect('frontend:staff_add')

        username = email
        onboarding_token = _generate_onboarding_token()
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
        )
        user.set_unusable_password()
        user.onboarding_completed = False
        user.onboarding_token = onboarding_token
        user.onboarding_token_created_at = timezone.now()
        user.is_active = False
        user.save()
        
        # Create staff profile
        staff = Staff.objects.create(
            user=user,
            staff_id=request.POST.get('staff_id'),
            staff_type=request.POST.get('staff_type', user_type),
            employment_type=request.POST.get('employment_type', 'full_time'),
            department=request.POST.get('department', ''),
            designation=request.POST.get('designation', ''),
            date_of_joining=request.POST.get('date_of_joining'),
            qualification=request.POST.get('qualification', ''),
            experience_years=request.POST.get('experience_years') or 0,
            gender=request.POST.get('gender', 'M'),
            marital_status=request.POST.get('marital_status', ''),
            bank_name=request.POST.get('bank_name', ''),
            account_number=request.POST.get('account_number', ''),
            tpin_no=request.POST.get('tpin_no', ''),
            nrc_no=request.POST.get('nrc_no', ''),
        )

        if request.FILES.get('nrc_front'):
            staff.nrc_front = request.FILES['nrc_front']
        if request.FILES.get('nrc_back'):
            staff.nrc_back = request.FILES['nrc_back']
        if request.FILES.get('other_documents'):
            staff.other_documents = request.FILES['other_documents']
        staff.save()

        onboarding_url = _send_staff_onboarding_email(request, user)
        
        if onboarding_url:
            messages.success(request, f'Staff member {staff.user.get_full_name()} added successfully. An onboarding link was sent to {staff.user.email}.')
        else:
            messages.warning(request, f'Staff member {staff.user.get_full_name()} added, but no email was available to send the onboarding link.')
        return redirect('frontend:staff_detail', pk=staff.pk)
    
    context = {
        'user_types': ['teacher', 'head_teacher', 'manager', 'auxiliary'],
        'staff_types': Staff.STAFF_TYPE_CHOICES,
        'employment_types': Staff.EMPLOYMENT_TYPE_CHOICES,
        'departments': ['Academic', 'Administration', 'Finance', 'IT', 'Maintenance', 'Security'],
        'genders': [('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
    }
    
    return render(request, 'frontend/staff/add.html', context)


def staff_onboarding_complete(request, token):
    """Public onboarding completion link for a newly invited staff member."""
    staff_member, user = _lookup_staff_for_completion(token=token)

    if request.method == 'POST':
        try:
            _finalize_staff_profile(request, staff_member, user, require_password=True)
            messages.success(request, 'Your account has been activated. You can now log in.')
            return redirect('frontend:dashboard')
        except ValueError as exc:
            messages.error(request, str(exc))

    context = _build_staff_profile_context(staff_member, require_password=True)
    return render(request, 'frontend/staff/complete_profile.html', context)


@manager_required
def staff_complete_profile(request, pk):
    """Manager/admin completion form for incomplete staff profiles."""
    staff_member, user = _lookup_staff_for_completion(pk=pk)

    if request.method == 'POST':
        try:
            _finalize_staff_profile(request, staff_member, user, require_password=True)
            messages.success(request, f'{staff_member.user.get_full_name()} profile completed successfully!')
            return redirect('frontend:staff_detail', pk=staff_member.pk)
        except ValueError as exc:
            messages.error(request, str(exc))

    context = _build_staff_profile_context(staff_member, require_password=False)
    return render(request, 'frontend/staff/complete_profile.html', context)


@manager_required
def staff_assign_classes(request, pk):
    """Assign classes to a staff member"""
    staff_member = get_object_or_404(Staff, pk=pk)
    
    if request.method == 'POST':
        class_ids = request.POST.getlist('classes')
        role = request.POST.get('role', 'teacher')
        
        for class_id in class_ids:
            classroom = ClassRoom.objects.get(id=class_id)
            if role == 'class_teacher':
                classroom.class_teacher = staff_member.user
                classroom.save()
            else:
                from .models_class_management import TeacherAssignment, AcademicYear
                current_year = AcademicYear.objects.filter(is_current=True).first()
                TeacherAssignment.objects.get_or_create(
                    teacher=staff_member.user,
                    classroom=classroom,
                    academic_year=current_year
                )
        
        messages.success(request, f'Classes assigned to {staff_member.user.get_full_name()} successfully!')
        return redirect('frontend:staff_detail', pk=pk)
    
    # Get all available classes
    classes = ClassRoom.objects.select_related('grade').all()
    
    # Get already assigned classes
    assigned_as_teacher = ClassRoom.objects.filter(class_teacher=staff_member)
    assigned_as_subject = ClassRoom.objects.filter(assigned_teachers=staff_member)
    
    context = {
        'staff': staff_member,
        'classes': classes,
        'assigned_as_teacher': assigned_as_teacher,
        'assigned_as_subject': assigned_as_subject,
    }
    
    return render(request, 'frontend/staff/assign_classes.html', context)


# ============================================
# STAFF DISCIPLINARY ACTIONS
# ============================================

@manager_required
def staff_disciplinary_action_list(request):
    """List all disciplinary actions"""
    actions = StaffDisciplinaryAction.objects.select_related('staff__user', 'reported_by', 'reviewed_by').all()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        actions = actions.filter(status=status_filter)
    
    # Filter by staff type
    staff_type = request.GET.get('staff_type', '')
    if staff_type:
        actions = actions.filter(staff__staff_type=staff_type)
    
    context = {
        'actions': actions,
        'status_filter': status_filter,
        'staff_type': staff_type,
        'statuses': StaffDisciplinaryAction.STATUS_CHOICES,
        'staff_types': Staff.STAFF_TYPE_CHOICES,
    }
    
    return render(request, 'frontend/staff/disciplinary_list.html', context)


@manager_required
def staff_disciplinary_action_report(request, pk):
    """Report a disciplinary action"""
    staff_member = get_object_or_404(Staff, pk=pk)
    
    if request.method == 'POST':
        action = StaffDisciplinaryAction.objects.create(
            staff=staff_member,
            action_type=request.POST.get('action_type'),
            severity=request.POST.get('severity'),
            reported_by=request.user,
            incident_date=request.POST.get('incident_date'),
            incident_description=request.POST.get('incident_description'),
            evidence=request.POST.get('evidence', ''),
        )
        messages.success(request, f'Disciplinary action reported for {staff_member.user.get_full_name()}')
        return redirect('frontend:staff_detail', pk=pk)
    
    context = {
        'staff': staff_member,
        'action_types': StaffDisciplinaryAction.ACTION_TYPE_CHOICES,
        'severities': StaffDisciplinaryAction.SEVERITY_CHOICES,
    }
    
    return render(request, 'frontend/staff/disciplinary_report.html', context)


@manager_required
def staff_disciplinary_action_detail(request, pk):
    """View and manage a disciplinary action"""
    action = get_object_or_404(StaffDisciplinaryAction, pk=pk)
    
    if request.method == 'POST':
        action.reviewed_by = request.user
        action.review_date = timezone.now().date()
        action.review_notes = request.POST.get('review_notes', '')
        action.status = request.POST.get('status', action.status)
        action.save()
        messages.success(request, 'Disciplinary action updated')
        return redirect('frontend:staff_disciplinary_detail', pk=pk)
    
    context = {
        'action': action,
        'statuses': StaffDisciplinaryAction.STATUS_CHOICES,
    }
    
    return render(request, 'frontend/staff/disciplinary_detail.html', context)


@manager_required
def staff_suspension_request_list(request):
    """List all suspension requests"""
    suspensions = StaffSuspensionRequest.objects.select_related('staff__user', 'requested_by', 'reviewed_by').all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        suspensions = suspensions.filter(status=status_filter)
    
    context = {
        'suspensions': suspensions,
        'status_filter': status_filter,
        'statuses': StaffSuspensionRequest.STATUS_CHOICES,
    }
    
    return render(request, 'frontend/staff/suspension_request_list.html', context)


@manager_required
def staff_suspension_request_create(request, pk):
    """Create a new suspension request for a staff member"""
    staff_member = get_object_or_404(Staff, pk=pk)
    
    if request.method == 'POST':
        start_date = request.POST.get('suspension_start_date')
        end_date = request.POST.get('suspension_end_date')
        
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        duration = (end - start).days
        
        suspension = StaffSuspensionRequest.objects.create(
            staff=staff_member,
            requested_by=request.user,
            reason=request.POST.get('reason'),
            suspension_start_date=start,
            suspension_end_date=end,
            duration_days=duration,
            pay_during_suspension=request.POST.get('pay_during_suspension', 'on') == 'on',
            benefits_during_suspension=request.POST.get('benefits_during_suspension', 'on') == 'on',
        )
        messages.success(request, f'Suspension request created for {staff_member.user.get_full_name()}')
        return redirect('frontend:staff_detail', pk=pk)
    
    context = {
        'staff': staff_member,
    }
    
    return render(request, 'frontend/staff/suspension_request_form.html', context)


@manager_required
def staff_suspension_request_detail(request, pk):
    """Review and approve/reject a suspension request"""
    suspension = get_object_or_404(StaffSuspensionRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            suspension.status = 'approved'
            suspension.reviewed_by = request.user
            suspension.review_date = timezone.now().date()
            suspension.review_comments = request.POST.get('review_comments', '')
            suspension.save()
            messages.success(request, 'Suspension request approved')
        elif action == 'reject':
            suspension.status = 'rejected'
            suspension.reviewed_by = request.user
            suspension.review_date = timezone.now().date()
            suspension.review_comments = request.POST.get('review_comments', '')
            suspension.save()
            messages.error(request, 'Suspension request rejected')
        
        return redirect('frontend:staff_suspension_request_detail', pk=pk)
    
    context = {
        'suspension': suspension,
    }
    
    return render(request, 'frontend/staff/suspension_request_detail.html', context)


@manager_required
def staff_termination_request_list(request):
    """List all termination requests"""
    terminations = StaffTerminationRequest.objects.select_related('staff__user', 'requested_by', 'reviewed_by').all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        terminations = terminations.filter(status=status_filter)
    
    context = {
        'terminations': terminations,
        'status_filter': status_filter,
        'statuses': StaffTerminationRequest.STATUS_CHOICES,
    }
    
    return render(request, 'frontend/staff/termination_request_list.html', context)


@manager_required
def staff_termination_request_create(request, pk):
    """Create a new termination request for a staff member"""
    staff_member = get_object_or_404(Staff, pk=pk)
    
    if request.method == 'POST':
        termination = StaffTerminationRequest.objects.create(
            staff=staff_member,
            requested_by=request.user,
            reason=request.POST.get('reason'),
            detailed_reason=request.POST.get('detailed_reason'),
            effective_date=request.POST.get('effective_date'),
            notice_period_days=request.POST.get('notice_period_days', 30),
            severance_type=request.POST.get('severance_type', 'full'),
            severance_amount=request.POST.get('severance_amount') or None,
            outstanding_leave_days=request.POST.get('outstanding_leave_days', 0),
            outstanding_leave_payment=request.POST.get('outstanding_leave_payment') or None,
        )
        messages.success(request, f'Termination request created for {staff_member.user.get_full_name()}')
        return redirect('frontend:staff_detail', pk=pk)
    
    context = {
        'staff': staff_member,
        'termination_reasons': StaffTerminationRequest.REASON_CHOICES,
        'severance_types': StaffTerminationRequest.SEVERANCE_TYPE_CHOICES,
    }
    
    return render(request, 'frontend/staff/termination_request_form.html', context)


@manager_required
def staff_termination_request_detail(request, pk):
    """Review and approve/reject a termination request"""
    termination = get_object_or_404(StaffTerminationRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            termination.status = 'approved'
            termination.reviewed_by = request.user
            termination.review_date = timezone.now().date()
            termination.review_comments = request.POST.get('review_comments', '')
            termination.save()
            messages.success(request, 'Termination request approved')
        elif action == 'reject':
            termination.status = 'rejected'
            termination.reviewed_by = request.user
            termination.review_date = timezone.now().date()
            termination.review_comments = request.POST.get('review_comments', '')
            termination.save()
            messages.error(request, 'Termination request rejected')
        
        return redirect('frontend:staff_termination_request_detail', pk=pk)
    
    context = {
        'termination': termination,
    }
    
    return render(request, 'frontend/staff/termination_request_detail.html', context)


@manager_required
def staff_promote_to_head(request, pk):
    """Promote a teacher to Head Teacher (manager only)"""
    staff_member = get_object_or_404(Staff.objects.select_related('user'), pk=pk)

    # Only allow promoting staff who are currently teachers
    if staff_member.staff_type != 'teacher' and staff_member.user.user_type != 'teacher':
        messages.error(request, 'Only staff members with type Teacher can be promoted to Head Teacher.')
        return redirect('frontend:staff_detail', pk=pk)

    if request.method == 'POST':
        # Update both User and Staff records
        user = staff_member.user
        user.user_type = 'head_teacher'
        user.save()

        staff_member.staff_type = 'head_teacher'
        staff_member.save()

        messages.success(request, f'{staff_member.user.get_full_name()} promoted to Head Teacher successfully!')
        return redirect('frontend:staff_detail', pk=pk)

    # Confirmation page
    context = {
        'staff': staff_member,
    }
    return render(request, 'frontend/staff/promote_confirm.html', context)
