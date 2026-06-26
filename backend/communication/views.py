from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from administration.decorators import role_required
from administration.models import User
from communication.models import Announcement, AppointmentRequest, EmailLog, Message, Newsletter, SMSLog


def _mark_approved(record, user, notes=''):
    approved_at = timezone.now()
    if hasattr(record, 'approval_status'):
        record.approval_status = 'approved'
        record.approved_by = user
        record.approved_at = approved_at
        if hasattr(record, 'approval_notes'):
            record.approval_notes = notes
        record.save()
    elif hasattr(record, 'status'):
        record.status = 'approved'
        record.responded_by = user
        record.responded_at = approved_at
        if hasattr(record, 'approval_notes'):
            record.approval_notes = notes
        record.save()


def _mark_rejected(record, user, notes=''):
    rejected_at = timezone.now()
    if hasattr(record, 'approval_status'):
        record.approval_status = 'rejected'
        record.approved_by = user
        record.approved_at = rejected_at
        if hasattr(record, 'approval_notes'):
            record.approval_notes = notes
        record.save()
    elif hasattr(record, 'status'):
        record.status = 'declined'
        record.responded_by = user
        record.responded_at = rejected_at
        if hasattr(record, 'approval_notes'):
            record.approval_notes = notes
        record.save()


def communication_hub(request):
    """Simple hub for announcements, messages, newsletters, and appointments."""
    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'announcement':
            from administration.notification_utils import send_approval_notification

            requires_approval = request.user.user_type not in {'manager', 'admin'}
            announcement = Announcement.objects.create(
                title=request.POST.get('title', '').strip(),
                content=request.POST.get('content', '').strip(),
                priority=request.POST.get('priority', 'normal'),
                target_audience=request.POST.get('target_audience', 'parents'),
                posted_by=request.user,
                approval_status='pending' if requires_approval else 'approved',
                approved_by=None if requires_approval else request.user,
                approved_at=None if requires_approval else timezone.now(),
            )
            if requires_approval:
                send_approval_notification(
                    notification_type='teacher_request',
                    title=f'Announcement Pending: {announcement.title[:50]}',
                    message=f'{request.user.get_full_name()} submitted announcement to {announcement.target_audience} for approval.',
                    related_object=announcement,
                    recipient_user_types=['admin', 'manager'],
                )
            messages.success(
                request,
                'Announcement submitted for approval.' if requires_approval else 'Announcement created successfully.',
            )
            return redirect('communication:announcement_list')

        if action_type == 'message':
            recipient_id = request.POST.get('recipient')
            if recipient_id:
                from administration.notification_utils import send_approval_notification

                requires_approval = request.user.user_type not in {'manager', 'admin'}
                recipient = get_object_or_404(User, pk=recipient_id)
                message_obj = Message.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=request.POST.get('subject', '').strip(),
                    body=request.POST.get('body', '').strip(),
                    approval_status='pending' if requires_approval else 'approved',
                    approved_by=None if requires_approval else request.user,
                    approved_at=None if requires_approval else timezone.now(),
                )
                if requires_approval:
                    send_approval_notification(
                        notification_type='teacher_request',
                        title=f'Message Pending: {message_obj.subject[:50]}',
                        message=f'{request.user.get_full_name()} sent message to {message_obj.recipient.get_full_name()} for approval.',
                        related_object=message_obj,
                        recipient_user_types=['admin', 'manager'],
                    )
                messages.success(
                    request,
                    'Message submitted for approval.' if requires_approval else 'Internal message sent.',
                )
            return redirect('communication:message_list')

        if action_type == 'reminder':
            audience = request.POST.get('audience', 'staff')
            subject = request.POST.get('subject', 'Reminder').strip()
            body = request.POST.get('body', '').strip()
            channel = request.POST.get('channel', 'email')

            if audience == 'staff':
                recipients = User.objects.filter(user_type__in=['manager', 'admin', 'head_teacher', 'teacher', 'auxiliary'])
            elif audience == 'parents':
                recipients = User.objects.filter(user_type='parent')
            else:
                recipients = User.objects.filter(user_type='student')

            created_count = 0
            for recipient in recipients:
                if channel == 'sms' and recipient.phone_number:
                    SMSLog.objects.create(
                        recipient=recipient,
                        phone_number=recipient.phone_number,
                        message=f'{subject}\n{body}',
                        status='pending',
                    )
                elif recipient.email:
                    EmailLog.objects.create(
                        recipient=recipient,
                        email_address=recipient.email,
                        subject=subject,
                        body=body,
                        status='pending',
                    )
                else:
                    continue
                created_count += 1

            messages.success(request, f'{created_count} reminder record(s) queued for delivery.')
            return redirect('communication:reminder_list')

        if action_type == 'newsletter':
            Newsletter.objects.create(
                title=request.POST.get('title', '').strip(),
                issue_number=request.POST.get('issue_number', '').strip(),
                content=request.POST.get('content', '').strip(),
                published_by=request.user,
                is_published=request.POST.get('is_published') == 'on',
                published_at=timezone.now(),
            )
            messages.success(request, 'Newsletter saved successfully.')
            return redirect('communication:newsletter_list')

        if action_type == 'appointment':
            from administration.notification_utils import send_approval_notification

            requires_approval = request.user.user_type not in {'manager', 'admin'}
            appointment = AppointmentRequest.objects.create(
                requested_by=request.user,
                meeting_with=request.POST.get('meeting_with', 'teacher'),
                specific_staff_id=request.POST.get('specific_staff') or None,
                subject=request.POST.get('subject', '').strip(),
                details=request.POST.get('details', '').strip(),
                preferred_date=request.POST.get('preferred_date'),
                preferred_time=request.POST.get('preferred_time') or None,
                duration_minutes=request.POST.get('duration_minutes') or 30,
                location=request.POST.get('location', '').strip(),
                status='pending' if requires_approval else 'approved',
                responded_by=None if requires_approval else request.user,
                responded_at=None if requires_approval else timezone.now(),
            )
            if requires_approval:
                send_approval_notification(
                    notification_type='teacher_request',
                    title=f'Appointment Request: {appointment.subject[:50]}',
                    message=f'{request.user.get_full_name()} requested an appointment for {appointment.preferred_date}.',
                    related_object=appointment,
                    recipient_user_types=['admin', 'manager'],
                )
            messages.success(
                request,
                'Appointment request submitted for approval.' if requires_approval else 'Appointment request submitted.',
            )
            return redirect('communication:communication_hub')

    context = {
        'announcements': Announcement.objects.filter(is_active=True).order_by('-posted_at')[:20],
        'messages_list': Message.objects.order_by('-sent_at')[:20],
        'newsletters': Newsletter.objects.filter(is_published=True).order_by('-published_at')[:20],
        'appointments': AppointmentRequest.objects.order_by('-created_at')[:20],
    }
    return render(request, 'frontend/communication/hub.html', context)


@role_required('teacher', 'head_teacher', 'manager', 'admin')
def teacher_communication_hub(request):
    """Teacher-only communication hub for parent communications and appointment requests."""
    parent_users = User.objects.filter(user_type='parent').order_by('first_name', 'last_name')

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'announcement':
            from administration.notification_utils import send_approval_notification

            announcement = Announcement.objects.create(
                title=request.POST.get('title', '').strip(),
                content=request.POST.get('content', '').strip(),
                priority=request.POST.get('priority', 'normal'),
                target_audience='parents',
                posted_by=request.user,
                approval_status='pending',
            )
            send_approval_notification(
                notification_type='teacher_request',
                title=f'Teacher Announcement Pending: {announcement.title[:50]}',
                message=f'{request.user.get_full_name()} submitted an announcement to parents for approval.',
                related_object=announcement,
                recipient_user_types=['admin', 'manager'],
            )
            messages.success(request, 'Parent announcement submitted for approval.')
            return redirect('communication:teacher_communication_hub')

        if action_type == 'message':
            from administration.notification_utils import send_approval_notification

            recipient_id = request.POST.get('recipient')
            if recipient_id:
                message_obj = Message.objects.create(
                    sender=request.user,
                    recipient=get_object_or_404(User, pk=recipient_id, user_type='parent'),
                    subject=request.POST.get('subject', '').strip(),
                    body=request.POST.get('body', '').strip(),
                    approval_status='pending',
                )
                send_approval_notification(
                    notification_type='teacher_request',
                    title=f'Teacher Message Pending: {message_obj.subject[:50]}',
                    message=f'{request.user.get_full_name()} sent a message to {message_obj.recipient.get_full_name()} pending approval.',
                    related_object=message_obj,
                    recipient_user_types=['admin', 'manager'],
                )
                messages.success(request, 'Parent message submitted for approval.')
            return redirect('communication:teacher_communication_hub')

        if action_type == 'appointment':
            from administration.notification_utils import send_approval_notification

            appointment = AppointmentRequest.objects.create(
                requested_by=request.user,
                meeting_with='management',
                subject=request.POST.get('subject', '').strip(),
                details=request.POST.get('details', '').strip(),
                preferred_date=request.POST.get('preferred_date'),
                preferred_time=request.POST.get('preferred_time') or None,
                duration_minutes=request.POST.get('duration_minutes') or 30,
                location=request.POST.get('location', '').strip(),
                status='pending',
            )
            send_approval_notification(
                notification_type='teacher_request',
                title=f'Appointment Request: {appointment.subject[:50]}',
                message=f'{request.user.get_full_name()} requested an appointment for {appointment.preferred_date}.',
                related_object=appointment,
                recipient_user_types=['admin', 'manager'],
            )
            messages.success(request, 'Appointment request submitted for approval.')
            return redirect('communication:teacher_communication_hub')

    context = {
        'parent_users': parent_users,
        'my_announcements': Announcement.objects.filter(posted_by=request.user).order_by('-posted_at')[:10],
        'my_messages': Message.objects.filter(sender=request.user).order_by('-sent_at')[:10],
        'my_appointments': AppointmentRequest.objects.filter(requested_by=request.user).order_by('-created_at')[:10],
    }
    return render(request, 'frontend/communication/teacher_hub.html', context)
