"""
Utility functions for sending notifications to admin and manager users
"""
from .models import Notification


def send_approval_notification(
    notification_type,
    title,
    message,
    related_object=None,
    recipient_user_types=['admin', 'manager']
):
    """
    Send a notification to all users of specified types (typically admin/manager).
    
    Args:
        notification_type: Type of notification (e.g., 'restocking_request')
        title: Short title for the notification
        message: Detailed message
        related_object: The object being notified about (RestockingRequest, EditRequest, etc.)
        recipient_user_types: List of user types to notify (default: admin and manager)
    
    Returns:
        List of created Notification objects
    """
    from .models import User
    
    # Get all recipients with specified user types
    recipients = User.objects.filter(user_type__in=recipient_user_types, is_active=True)
    
    notifications = []
    content_type = related_object.__class__.__name__ if related_object else ''
    object_id = related_object.id if related_object else None
    
    for recipient in recipients:
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            content_type=content_type,
            object_id=object_id,
        )
        notifications.append(notification)
    
    return notifications


def get_pending_notifications_count(user):
    """
    Get count of unread notifications for a user
    """
    return Notification.objects.filter(
        recipient=user,
        status='unread'
    ).count()


def get_pending_notifications(user, limit=10):
    """
    Get unread notifications for a user, ordered by most recent
    """
    return Notification.objects.filter(
        recipient=user,
        status='unread'
    ).order_by('-created_at')[:limit]
