from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from .models import StudentAttendance, StaffAttendance, AttendanceSummary
from administration.models import Student, Staff, ClassRoom
from administration.permissions import UserHierarchy
from datetime import datetime, date


def _is_school_leader(user):
    return user.is_superuser or user.user_type in {'admin', 'manager', 'head_teacher'}


def _teacher_accessible_classes(user):
    if _is_school_leader(user):
        return ClassRoom.objects.select_related('grade').all()
    if user.user_type == 'teacher':
        return UserHierarchy.get_accessible_classes(user).select_related('grade')
    return ClassRoom.objects.none()

@login_required
def student_attendance_list(request):
    """List student attendance"""
    attendance = StudentAttendance.objects.select_related(
        'student', 'classroom'
    ).order_by('-date')

    if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
        attendance = attendance.filter(classroom__in=_teacher_accessible_classes(request.user))
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        attendance = attendance.filter(date=date_filter)
    else:
        attendance = attendance.filter(date=date.today())
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
            accessible_class_ids = set(_teacher_accessible_classes(request.user).values_list('pk', flat=True))
            if int(class_id) not in accessible_class_ids:
                class_id = None
        if class_id:
            attendance = attendance.filter(classroom_id=class_id)
    
    classes = _teacher_accessible_classes(request.user) if request.user.user_type == 'teacher' and not _is_school_leader(request.user) else ClassRoom.objects.filter(
        academic_year__is_current=True
    ).select_related('grade')
    
    context = {
        'attendance': attendance[:200],
        'classes': classes,
        'selected_date': date_filter or date.today(),
    }
    
    return render(request, 'attendance/student_attendance_list.html', context)

@login_required
def mark_attendance(request):
    """Mark attendance for a class"""
    teacher_classes = _teacher_accessible_classes(request.user)
    teacher_class = teacher_classes.first() if request.user.user_type == 'teacher' and not _is_school_leader(request.user) else None

    if request.method == 'POST':
        class_id = request.POST.get('class_room') or getattr(teacher_class, 'pk', None)
        attendance_date = request.POST.get('date', date.today())

        if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
            if not class_id or int(class_id) not in set(teacher_classes.values_list('pk', flat=True)):
                messages.error(request, 'You can only mark attendance for your assigned class.')
                return redirect('frontend:attendance_mark')
        
        classroom = ClassRoom.objects.get(id=class_id)
        students = Student.objects.filter(current_class=classroom, status='enrolled')
        
        for student in students:
            status = request.POST.get(f'status_{student.pk}', 'absent')
            remarks = request.POST.get(f'remarks_{student.pk}', '')
            
            StudentAttendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    'classroom': classroom,
                    'status': status,
                    'remarks': remarks,
                    'marked_by': request.user
                }
            )
        
        messages.success(request, 'Attendance marked successfully!')
        return redirect('frontend:attendance_list')
    
    classes = teacher_classes if request.user.user_type == 'teacher' and not _is_school_leader(request.user) else ClassRoom.objects.select_related('grade').all()
    
    class_id = request.GET.get('class')
    students = None
    selected_class = None
    
    if class_id:
        if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
            accessible_class_ids = set(teacher_classes.values_list('pk', flat=True))
            if int(class_id) not in accessible_class_ids:
                selected_class = teacher_class or teacher_classes.first()
                class_id = getattr(selected_class, 'pk', None)
        if class_id:
            selected_class = ClassRoom.objects.get(id=class_id)
        students = Student.objects.filter(
            current_class=selected_class,
            status='enrolled'
        ).select_related('user')
    
    context = {
        'classes': classes,
        'students': students,
        'selected_class': selected_class,
        'teacher_class': teacher_class,
        'today': date.today(),
    }
    
    return render(request, 'attendance/mark_attendance.html', context)

@login_required
def staff_attendance_list(request):
    """List staff attendance"""
    attendance = StaffAttendance.objects.select_related(
        'staff', 'staff__user'
    ).order_by('-date')
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter:
        attendance = attendance.filter(date=date_filter)
    else:
        attendance = attendance.filter(date=date.today())
    
    context = {
        'attendance': attendance[:100],
        'selected_date': date_filter or date.today(),
    }
    
    return render(request, 'attendance/staff_attendance_list.html', context)

@login_required
def attendance_summary(request):
    """Attendance summary report"""
    summaries = AttendanceSummary.objects.select_related(
        'student', 'student__user', 'class_room'
    ).order_by('-month', '-year')
    
    # Filter by month/year if provided
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if month:
        summaries = summaries.filter(month=month)
    if year:
        summaries = summaries.filter(year=year)
    
    context = {
        'summaries': summaries[:100],
    }
    
    return render(request, 'attendance/attendance_summary.html', context)
