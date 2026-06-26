from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.http import JsonResponse
from .models import Subject, Exam, ExamResult, ReportCard, Timetable
from administration.models import Student, AcademicYear, Term, ClassRoom, User
from attendance.models import StudentAttendance
from administration.decorators import role_required, teacher_or_above
from administration.permissions import UserHierarchy
from portals.models import EventCalendar
from django.utils import timezone
from typing import Any, cast


def _is_school_leader(user):
    return user.is_superuser or user.user_type in {'admin', 'manager', 'head_teacher'}


def _teacher_accessible_classes(user):
    if _is_school_leader(user):
        return ClassRoom.objects.select_related('grade', 'academic_year').all()
    if user.user_type == 'teacher':
        return UserHierarchy.get_accessible_classes(user).select_related('grade', 'academic_year')
    return ClassRoom.objects.none()

@login_required
def subject_list(request):
    """List all subjects"""
    subjects = Subject.objects.all().order_by('name')
    
    context = {
        'subjects': subjects,
    }
    
    return render(request, 'academics/subject_list.html', context)

@login_required
def exam_list(request):
    """List all exams"""
    exams = Exam.objects.select_related(
        'subject', 'classroom', 'term'
    ).order_by('-exam_date')

    if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
        exams = exams.filter(classroom__in=_teacher_accessible_classes(request.user))
    
    # Filter by term if provided
    term_id = request.GET.get('term')
    if term_id:
        exams = exams.filter(term_id=term_id)
    
    context = {
        'exams': exams,
    }
    
    return render(request, 'academics/exam_list.html', context)


@teacher_or_above
def exam_create(request):
    """Log a class exam after it has been administered."""
    is_teacher = request.user.user_type == 'teacher'
    teacher_classes = _teacher_accessible_classes(request.user) if is_teacher else ClassRoom.objects.select_related('grade', 'academic_year').all()
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(academic_year=current_year, is_current=True).first() if current_year else None

    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        if is_teacher:
            allowed_ids = set(teacher_classes.values_list('pk', flat=True))
            classroom_id = classroom_id or getattr(teacher_classes.first(), 'pk', None)
            if classroom_id and int(classroom_id) not in allowed_ids:
                messages.error(request, 'You can only log exams for your assigned class.')
                return redirect('frontend:exam_create')

        exam = Exam.objects.create(
            name=request.POST.get('name', '').strip(),
            exam_type=request.POST.get('exam_type', 'mid_term'),
            subject_id=request.POST.get('subject'),
            classroom_id=classroom_id,
            term_id=request.POST.get('term') or getattr(current_term, 'pk', None),
            exam_date=request.POST.get('exam_date'),
            start_time=request.POST.get('start_time'),
            duration_minutes=request.POST.get('duration_minutes') or 60,
            max_marks=request.POST.get('max_marks') or 100,
            pass_marks=request.POST.get('pass_marks') or 40,
            instructions=request.POST.get('instructions', '').strip(),
            syllabus_covered=request.POST.get('syllabus_covered', '').strip(),
            is_administered=request.POST.get('is_administered') == 'on' or is_teacher,
            administered_at=timezone.now() if (request.POST.get('is_administered') == 'on' or is_teacher) else None,
            administered_by=request.user if (request.POST.get('is_administered') == 'on' or is_teacher) else None,
            created_by=request.user,
        )
        messages.success(request, f'Exam logged successfully: {exam.name}')
        return redirect('frontend:exam_list')

    return render(request, 'academics/exam_create.html', {
        'subjects': Subject.objects.all().order_by('name'),
        'classrooms': teacher_classes,
        'terms': Term.objects.select_related('academic_year').all().order_by('academic_year', 'term_number'),
        'exam_types': Exam.EXAM_TYPE_CHOICES,
        'current_year': current_year,
        'current_term': current_term,
        'is_teacher': is_teacher,
    })

@login_required
def result_list(request):
    """List exam results"""
    results = ExamResult.objects.select_related(
        'exam', 'exam__subject', 'student', 'student__user'
    ).order_by('-exam__exam_date')

    if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
        results = results.filter(exam__classroom__in=_teacher_accessible_classes(request.user))
    
    # Filter by student if provided
    student_id = request.GET.get('student')
    if student_id:
        results = results.filter(student_id=student_id)
    
    # Filter by exam if provided
    exam_id = request.GET.get('exam')
    if exam_id:
        results = results.filter(exam_id=exam_id)
    
    context = {
        'results': results[:100],  # Limit to 100 results
    }
    
    return render(request, 'academics/result_list.html', context)

@login_required
def result_detail(request, pk):
    """Exam result detail"""
    result = get_object_or_404(
        ExamResult.objects.select_related(
            'exam', 'exam__subject', 'student', 'student__user'
        ),
        pk=pk
    )
    
    # Get class average for this exam
    class_average = ExamResult.objects.filter(
        exam=result.exam
    ).aggregate(avg=Avg('marks_obtained'))['avg'] or 0
    
    context = {
        'result': result,
        'class_average': round(class_average, 2),
    }
    
    return render(request, 'academics/result_detail.html', context)


@login_required
def timetable_view(request):
    """Academic timetable overview with real class schedule data."""
    timetable = Timetable.objects.select_related(
        'classroom',
        'classroom__grade',
        'subject',
        'teacher',
        'academic_year',
        'term',
    ).filter(is_active=True).order_by('day_of_week', 'start_time')

    context = {
        'timetable': timetable,
    }
    return render(request, 'academics/timetable.html', context)


@teacher_or_above
def timetable_create(request):
    """Create a timetable entry for a class."""
    is_teacher = request.user.user_type == 'teacher'
    teacher_classes = _teacher_accessible_classes(request.user) if is_teacher else ClassRoom.objects.select_related('grade', 'academic_year').all()

    if request.method == 'POST':
        classroom_id = request.POST.get('classroom')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher') or request.user.pk
        academic_year_id = request.POST.get('academic_year')
        term_id = request.POST.get('term') or None

        if is_teacher:
            classroom_id = request.POST.get('classroom') or getattr(teacher_classes.first(), 'pk', None)
            if classroom_id and int(classroom_id) not in set(teacher_classes.values_list('pk', flat=True)):
                messages.error(request, 'You can only create timetable entries for your assigned class.')
                return redirect('frontend:timetable_create')

        Timetable.objects.create(
            classroom_id=classroom_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            academic_year_id=academic_year_id,
            term_id=term_id,
            day_of_week=request.POST.get('day_of_week'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            room=request.POST.get('room', ''),
            notes=request.POST.get('notes', ''),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Timetable entry created successfully.')
        return redirect('frontend:timetable')

    return render(request, 'academics/timetable_create.html', {
        'classrooms': teacher_classes,
        'subjects': Subject.objects.all().order_by('name'),
        'teachers': User.objects.filter(user_type='teacher').order_by('first_name', 'last_name'),
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'terms': Term.objects.select_related('academic_year').all().order_by('academic_year', 'term_number'),
        'is_teacher': is_teacher,
    })


@login_required
def academic_calendar_view(request):
    """School event calendar using the existing portals.EventCalendar model."""
    events = EventCalendar.objects.select_related('created_by', 'approved_by').all().order_by('start_date', 'start_time')

    if _is_school_leader(request.user):
        visible_events = events
    else:
        visible_events = events.filter(Q(approval_status='approved') | Q(created_by=request.user))

    if request.method == 'POST' and _is_school_leader(request.user):
        event_id = request.POST.get('event_id')
        action = request.POST.get('action')
        event = get_object_or_404(EventCalendar, pk=event_id)
        if action == 'approve':
            event.approval_status = 'approved'
            event.approved_by = request.user
            event.approved_at = timezone.now()
            event.save(update_fields=['approval_status', 'approved_by', 'approved_at'])
            messages.success(request, 'Calendar event approved.')
        elif action == 'reject':
            event.approval_status = 'rejected'
            event.approved_by = request.user
            event.approved_at = timezone.now()
            event.approval_notes = request.POST.get('approval_notes', '')
            event.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'approval_notes'])
            messages.success(request, 'Calendar event rejected.')
        return redirect('frontend:calendar')

    context = {
        'events': visible_events,
        'pending_events': events.filter(approval_status='pending'),
    }
    return render(request, 'academics/calendar.html', context)


@teacher_or_above
def academic_calendar_create(request):
    """Create a school event; teacher/head-teacher submissions require approval."""
    if request.method == 'POST':
        from administration.services import ApprovalService
        
        requires_approval = request.user.user_type == 'teacher'
        event = EventCalendar.objects.create(
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            event_type=request.POST.get('event_type', 'other'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            start_time=request.POST.get('start_time') or None,
            end_time=request.POST.get('end_time') or None,
            location=request.POST.get('location', '').strip(),
            is_public=request.POST.get('is_public') == 'on',
            created_by=request.user,
            approval_status='pending' if requires_approval else 'approved',
            approved_by=None if requires_approval else request.user,
            approved_at=None if requires_approval else timezone.now(),
            approval_notes='',
        )
        
        if requires_approval:
            ApprovalService.create_request(
                instance=event,
                request_type='event',
                reviewers=User.objects.filter(user_type__in=['admin', 'manager']),
                requested_by=request.user,
                remarks=event.description,
            )

        messages.success(request, 'Event created. It will appear after approval if required.')
        return redirect('frontend:calendar')

    return render(request, 'academics/calendar_create.html', {
        'event_types': EventCalendar.EVENT_TYPE_CHOICES,
        'requires_approval': request.user.user_type == 'teacher',
    })


@teacher_or_above
def timetable_edit(request, pk):
    """Edit a timetable entry.

    Teachers may edit entries for their own class. Head teachers, managers, and admins
    can edit any entry, but their changes require an explicit confirmation step.
    """
    timetable_entry = get_object_or_404(
        Timetable.objects.select_related('classroom', 'classroom__grade', 'subject', 'teacher', 'academic_year', 'term'),
        pk=pk,
    )

    is_teacher = request.user.user_type == 'teacher'
    can_edit_own_class = is_teacher and getattr(timetable_entry.classroom, 'class_teacher_id', None) == request.user.pk
    can_edit_any = request.user.user_type in {'admin', 'manager', 'head_teacher'}

    if not (can_edit_own_class or can_edit_any):
        messages.error(request, 'You do not have permission to edit this timetable entry.')
        return redirect('frontend:timetable')

    if request.method == 'POST':
        requires_extra_confirmation = can_edit_any and not is_teacher
        edit_reason = (request.POST.get('edit_reason') or '').strip()
        confirmed = request.POST.get('confirm_changes') == 'on'

        if requires_extra_confirmation and not edit_reason:
            return render(request, 'academics/timetable_edit.html', {
                'timetable_entry': timetable_entry,
                'requires_extra_confirmation': requires_extra_confirmation,
                'error_message': 'Please provide a reason for this timetable edit.',
            })

        if requires_extra_confirmation and not confirmed:
            return render(request, 'academics/timetable_edit.html', {
                'timetable_entry': timetable_entry,
                'requires_extra_confirmation': requires_extra_confirmation,
                'error_message': 'Please confirm the timetable changes before saving.',
            })

        classroom_id = request.POST.get('classroom')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        academic_year_id = request.POST.get('academic_year')
        term_id = request.POST.get('term')

        if classroom_id:
            timetable_entry.classroom = ClassRoom.objects.get(pk=classroom_id)
        if subject_id:
            timetable_entry.subject = Subject.objects.get(pk=subject_id)
        if teacher_id:
            timetable_entry.teacher = User.objects.get(pk=teacher_id)
        if academic_year_id:
            timetable_entry.academic_year = AcademicYear.objects.get(pk=academic_year_id)
        if term_id:
            timetable_entry.term = Term.objects.get(pk=term_id)
        timetable_entry.day_of_week = request.POST.get('day_of_week') or timetable_entry.day_of_week
        timetable_entry.start_time = request.POST.get('start_time') or timetable_entry.start_time
        timetable_entry.end_time = request.POST.get('end_time') or timetable_entry.end_time
        timetable_entry.room = request.POST.get('room', timetable_entry.room)
        timetable_entry.notes = request.POST.get('notes', timetable_entry.notes)
        timetable_entry.is_active = request.POST.get('is_active') == 'on'
        timetable_entry.save()

        if requires_extra_confirmation:
            messages.success(request, f'Timetable entry updated after review: {edit_reason}')
        else:
            messages.success(request, 'Timetable entry updated successfully.')
        return redirect('frontend:timetable')

    return render(request, 'academics/timetable_edit.html', {
        'timetable_entry': timetable_entry,
        'requires_extra_confirmation': can_edit_any and not is_teacher,
        'classrooms': ClassRoom.objects.select_related('grade', 'academic_year').all().order_by('grade__level', 'section'),
        'subjects': Subject.objects.all().order_by('name'),
        'teachers': User.objects.filter(user_type='teacher').order_by('first_name', 'last_name'),
        'academic_years': AcademicYear.objects.all().order_by('-start_date'),
        'terms': Term.objects.select_related('academic_year').all().order_by('academic_year', 'term_number'),
    })


@login_required
def check_timetable_conflicts(request):
    """
    API endpoint to check for timetable conflicts in real-time.
    Returns JSON with conflicts found.
    """
    classroom_id = request.GET.get('classroom')
    teacher_id = request.GET.get('teacher')
    day_of_week = request.GET.get('day_of_week')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    room = request.GET.get('room')
    academic_year_id = request.GET.get('academic_year')
    timetable_id = request.GET.get('timetable_id')  # For editing - exclude self
    
    conflicts = {
        'has_conflicts': False,
        'classroom_conflict': None,
        'teacher_conflict': None,
        'room_conflict': None,
    }
    
    if not all([classroom_id, day_of_week, start_time, end_time, academic_year_id]):
        return JsonResponse(conflicts)
    
    try:
        # Build base query
        query = Q(
            day_of_week=day_of_week,
            academic_year_id=academic_year_id,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        
        # Check classroom conflicts
        classroom_conflicts = Timetable.objects.filter(
            Q(classroom_id=classroom_id),
            query
        ).exclude(pk=timetable_id) if timetable_id else Timetable.objects.filter(Q(classroom_id=classroom_id), query)
        
        if classroom_conflicts.exists():
            conflict = classroom_conflicts.first()
            if conflict is not None:
                conflict = cast(Any, conflict)
                conflicts['classroom_conflict'] = {
                    'subject': str(conflict.subject),
                    'teacher': conflict.teacher.get_full_name() if conflict.teacher else 'Unassigned',
                    'time': f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')}",
                }
                conflicts['has_conflicts'] = True
        
        # Check teacher conflicts
        if teacher_id:
            teacher_conflicts = Timetable.objects.filter(
                Q(teacher_id=teacher_id),
                query
            ).exclude(pk=timetable_id) if timetable_id else Timetable.objects.filter(Q(teacher_id=teacher_id), query)
            
            if teacher_conflicts.exists():
                conflict = teacher_conflicts.first()
                if conflict is not None:
                    conflict = cast(Any, conflict)
                    conflicts['teacher_conflict'] = {
                        'class': str(conflict.classroom),
                        'subject': str(conflict.subject),
                        'time': f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')}",
                    }
                    conflicts['has_conflicts'] = True
        
        # Check room conflicts
        if room:
            room_conflicts = Timetable.objects.filter(
                Q(room=room),
                query
            ).exclude(pk=timetable_id) if timetable_id else Timetable.objects.filter(Q(room=room), query)
            
            if room_conflicts.exists():
                conflict = room_conflicts.first()
                if conflict is not None:
                    conflict = cast(Any, conflict)
                    conflicts['room_conflict'] = {
                        'class': str(conflict.classroom),
                        'subject': str(conflict.subject),
                        'teacher': conflict.teacher.get_full_name() if conflict.teacher else 'Unassigned',
                        'time': f"{conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')}",
                    }
                    conflicts['has_conflicts'] = True
    
    except Exception as e:
        conflicts['error'] = str(e)
    
    return JsonResponse(conflicts)


def _grade_from_percentage(percentage):
    if percentage >= 90:
        return 'A+'
    if percentage >= 80:
        return 'A'
    if percentage >= 70:
        return 'B'
    if percentage >= 60:
        return 'C'
    if percentage >= 50:
        return 'D'
    if percentage >= 40:
        return 'E'
    return 'F'


def _comment_from_percentage(percentage):
    if percentage >= 90:
        return 'Excellent performance. Keep it up.'
    if percentage >= 80:
        return 'Very good work with strong understanding.'
    if percentage >= 70:
        return 'Good performance with room for improvement.'
    if percentage >= 60:
        return 'Satisfactory performance. More effort is needed.'
    if percentage >= 50:
        return 'Passable, but needs consistent improvement.'
    return 'Needs urgent academic support and guidance.'


@login_required
def exam_score_entry(request, pk):
    """Enter or update scores for students in a specific exam."""
    exam = get_object_or_404(
        Exam.objects.select_related('subject', 'classroom', 'classroom__grade', 'term'),
        pk=pk,
    )
    if request.user.user_type == 'teacher' and not _is_school_leader(request.user):
        accessible_class_ids = set(_teacher_accessible_classes(request.user).values_list('pk', flat=True))
        if getattr(exam.classroom, 'pk', None) not in accessible_class_ids:
            messages.error(request, 'You can only enter scores for your assigned classes.')
            return redirect('frontend:exam_list')

    students = Student.objects.filter(
        current_class=exam.classroom,
        status='active',
    ).select_related('user', 'current_class')

    if not exam.is_administered:
        messages.warning(request, 'This exam must be marked as administered before scores can be entered.')

    existing_results = {
        getattr(result, 'student_id', None) or getattr(result.student, 'pk', None): result
        for result in ExamResult.objects.filter(exam=exam, student__in=students)
    }

    if request.method == 'POST':
        if not exam.is_administered:
            messages.error(request, 'Mark the exam as administered before saving scores.')
            return redirect('frontend:exam_score_entry', pk=exam.pk)

        updated_count = 0
        for student in students:
            raw_marks = (request.POST.get(f'marks_{student.pk}') or '').strip()
            is_absent = request.POST.get(f'absent_{student.pk}') == 'on'

            if not raw_marks and not is_absent:
                continue

            marks_value = None
            if raw_marks and not is_absent:
                marks_value = Decimal(raw_marks)

            ExamResult.objects.update_or_create(
                exam=exam,
                student=student,
                defaults={
                    'marks_obtained': marks_value,
                    'is_absent': is_absent,
                },
            )
            updated_count += 1

        messages.success(request, f'{updated_count} score record(s) saved successfully.')
        return redirect('frontend:exam_list')

    context = {
        'exam': exam,
        'students': students,
        'existing_results': existing_results,
    }
    return render(request, 'academics/exam_score_entry.html', context)


@login_required
def report_card_view(request, student_id):
    """Generate a report card summary for a student and term."""
    student = get_object_or_404(
        Student.objects.select_related('user', 'current_class', 'current_class__grade'),
        pk=student_id,
    )

    term_id = request.GET.get('term')
    current_term = None
    if term_id:
        current_term = get_object_or_404(Term, pk=term_id)
    elif student.current_class:
        current_term = Term.objects.filter(
            academic_year=student.current_class.academic_year,
            is_current=True,
        ).first()

    if not current_term:
        messages.error(request, 'No active term found for this student.')
        return redirect('frontend:student_detail', pk=student.pk)

    results = ExamResult.objects.filter(
        student=student,
        exam__term=current_term,
    ).select_related('exam', 'exam__subject').order_by('exam__subject__name', 'exam__exam_date')

    subject_rows = []
    total_percentage = Decimal('0')
    graded_items = 0

    for result in results:
        if result.is_absent or result.marks_obtained is None or result.exam.max_marks == 0:
            percentage = Decimal('0')
        else:
            percentage = (Decimal(result.marks_obtained) / Decimal(result.exam.max_marks)) * Decimal('100')
            total_percentage += percentage
            graded_items += 1

        subject_rows.append({
            'exam': result.exam,
            'marks_obtained': result.marks_obtained,
            'max_marks': result.exam.max_marks,
            'percentage': round(percentage, 2),
            'grade': _grade_from_percentage(float(percentage)),
            'is_absent': result.is_absent,
        })

    overall_percentage = (total_percentage / graded_items) if graded_items else Decimal('0')
    attendance_total = StudentAttendance.objects.filter(
        student=student,
        date__gte=current_term.start_date,
        date__lte=current_term.end_date,
    ).count()
    attendance_present = StudentAttendance.objects.filter(
        student=student,
        date__gte=current_term.start_date,
        date__lte=current_term.end_date,
        status='present',
    ).count()
    attendance_percentage = (
        (Decimal(attendance_present) / Decimal(attendance_total)) * Decimal('100')
        if attendance_total else Decimal('0')
    )

    report_card, _ = ReportCard.objects.update_or_create(
        student=student,
        term=current_term,
        defaults={
            'classroom': student.current_class,
            'overall_percentage': round(float(overall_percentage), 2),
            'overall_grade': _grade_from_percentage(float(overall_percentage)),
            'attendance_percentage': round(float(attendance_percentage), 2),
            'conduct_grade': 'A',
            'teacher_remarks': _comment_from_percentage(float(overall_percentage)),
            'principal_remarks': 'Generated from current academic records.',
        },
    )

    context = {
        'student': student,
        'term': current_term,
        'report_card': report_card,
        'subject_rows': subject_rows,
        'overall_percentage': round(float(overall_percentage), 2),
        'overall_grade': _grade_from_percentage(float(overall_percentage)),
        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_percentage': round(float(attendance_percentage), 2),
        'comment': _comment_from_percentage(float(overall_percentage)),
    }
    return render(request, 'academics/report_card.html', context)


@teacher_or_above
def report_card_edit(request, pk):
    """Edit an existing report card with an extra confirmation step."""
    report_card = get_object_or_404(
        ReportCard.objects.select_related('student', 'student__user', 'term', 'classroom', 'classroom__grade'),
        pk=pk,
    )

    is_teacher = request.user.user_type == 'teacher'
    can_edit_own_class = is_teacher and getattr(report_card.classroom, 'class_teacher_id', None) == request.user.pk
    can_edit_any = request.user.user_type in {'admin', 'manager', 'head_teacher'}

    if not (can_edit_own_class or can_edit_any):
        messages.error(request, 'You do not have permission to edit this report card.')
        return redirect('frontend:report_card_view', student_id=report_card.student.pk)

    if request.method == 'POST':
        requires_extra_confirmation = can_edit_any and not is_teacher
        edit_reason = (request.POST.get('edit_reason') or '').strip()
        confirmed = request.POST.get('confirm_changes') == 'on'

        if requires_extra_confirmation and not edit_reason:
            return render(request, 'academics/report_card_edit.html', {
                'report_card': report_card,
                'requires_extra_confirmation': requires_extra_confirmation,
                'error_message': 'Please provide a reason for this edit.',
            })

        if requires_extra_confirmation and not confirmed:
            return render(request, 'academics/report_card_edit.html', {
                'report_card': report_card,
                'requires_extra_confirmation': requires_extra_confirmation,
                'error_message': 'Please confirm the changes before saving.',
            })

        report_card.overall_percentage = request.POST.get('overall_percentage') or report_card.overall_percentage
        report_card.overall_grade = request.POST.get('overall_grade') or report_card.overall_grade
        report_card.attendance_percentage = request.POST.get('attendance_percentage') or report_card.attendance_percentage
        report_card.conduct_grade = request.POST.get('conduct_grade') or report_card.conduct_grade
        report_card.teacher_remarks = request.POST.get('teacher_remarks', report_card.teacher_remarks)
        report_card.principal_remarks = request.POST.get('principal_remarks', report_card.principal_remarks)
        report_card.position_in_class = request.POST.get('position_in_class') or report_card.position_in_class
        report_card.save()

        if requires_extra_confirmation:
            messages.success(request, f'Report card updated after review. Note: {edit_reason}')
        else:
            messages.success(request, 'Report card updated successfully.')
        return redirect('frontend:report_card_view', student_id=report_card.student.pk)

    return render(request, 'academics/report_card_edit.html', {
        'report_card': report_card,
        'requires_extra_confirmation': can_edit_any and not is_teacher,
    })
