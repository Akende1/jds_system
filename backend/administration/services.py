from django.contrib.contenttypes.models import ContentType

from .models import ApprovalRequest, Notification
from .notification_utils import send_approval_notification


class ApprovalService:
    @staticmethod
    def create_request(instance, request_type, reviewers, requested_by, remarks=''):
        content_type = ContentType.objects.get_for_model(instance.__class__)
        approval_request = ApprovalRequest.objects.create(
            request_type=request_type,
            content_type=content_type,
            object_id=instance.pk,
            requested_by=requested_by,
            remarks=remarks,
        )
        approval_request.assigned_to.set(reviewers)

        title = f'{approval_request.get_request_type_display()}: {instance}'
        message = f'{requested_by.get_full_name()} submitted a {approval_request.get_request_type_display().lower()} for review.'
        send_approval_notification(
            notification_type='other',
            title=title,
            message=message,
            related_object=instance,
            recipient_user_types=[user.user_type for user in reviewers] if reviewers else ['admin', 'manager'],
        )
        return approval_request

    @staticmethod
    def approve(approval_request, user, reason=''):
        from django.utils import timezone

        approval_request.status = 'approved'
        approval_request.reviewed_by = user
        approval_request.reviewed_at = timezone.now()
        if reason:
            approval_request.remarks = reason
        approval_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'remarks'])

        target = approval_request.content_object
        if hasattr(target, 'approval_status'):
            target.approval_status = 'approved'
            if hasattr(target, 'approved_by'):
                target.approved_by = user
            if hasattr(target, 'approved_at'):
                from django.utils import timezone
                target.approved_at = timezone.now()
            update_fields = []
            for field_name in ['approval_status', 'approved_by', 'approved_at']:
                if hasattr(target, field_name):
                    update_fields.append(field_name)
            if update_fields:
                target.save(update_fields=update_fields)
        elif hasattr(target, 'status'):
            target.status = 'approved'
            if hasattr(target, 'reviewed_by'):
                target.reviewed_by = user
            if hasattr(target, 'reviewed_at'):
                from django.utils import timezone
                target.reviewed_at = timezone.now()
            update_fields = ['status']
            if hasattr(target, 'reviewed_by'):
                update_fields.append('reviewed_by')
            if hasattr(target, 'reviewed_at'):
                update_fields.append('reviewed_at')
            target.save(update_fields=update_fields)

        return approval_request

    @staticmethod
    def reject(approval_request, user, reason=''):
        from django.utils import timezone

        approval_request.status = 'rejected'
        approval_request.reviewed_by = user
        approval_request.reviewed_at = timezone.now()
        if reason:
            approval_request.remarks = reason
        approval_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'remarks'])

        target = approval_request.content_object
        if hasattr(target, 'approval_status'):
            target.approval_status = 'rejected'
            if hasattr(target, 'approved_by'):
                target.approved_by = user
            if hasattr(target, 'approval_notes'):
                target.approval_notes = reason
            update_fields = []
            for field_name in ['approval_status', 'approved_by', 'approval_notes']:
                if hasattr(target, field_name):
                    update_fields.append(field_name)
            if update_fields:
                target.save(update_fields=update_fields)
        elif hasattr(target, 'status'):
            target.status = 'rejected'
            if hasattr(target, 'reviewed_by'):
                target.reviewed_by = user
            if hasattr(target, 'reviewed_at'):
                from django.utils import timezone
                target.reviewed_at = timezone.now()
            if hasattr(target, 'admin_notes'):
                target.admin_notes = reason
            update_fields = ['status']
            if hasattr(target, 'reviewed_by'):
                update_fields.append('reviewed_by')
            if hasattr(target, 'reviewed_at'):
                update_fields.append('reviewed_at')
            if hasattr(target, 'admin_notes'):
                update_fields.append('admin_notes')
            target.save(update_fields=update_fields)

        return approval_request
