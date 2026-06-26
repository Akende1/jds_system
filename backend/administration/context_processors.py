from datetime import date

from .permissions import UserHierarchy


def current_date_context(request):
    """Expose the current date to all templates."""
    return {
        'today': date.today(),
    }


def notification_context(request):
    """Add pending notifications count and list to all templates for admin/manager users."""
    try:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return {}
        
        # Only show notifications for admin and manager
        if user.user_type not in ['admin', 'manager']:
            return {}
        
        from .models import Notification
        from .notification_utils import get_pending_notifications_count, get_pending_notifications
        
        pending_count = get_pending_notifications_count(user)
        recent_notifications = get_pending_notifications(user, limit=5)
        
        return {
            'pending_notifications_count': pending_count,
            'recent_notifications': recent_notifications,
        }
    except Exception:
        # If there's any error loading notifications, just return empty dict
        # This prevents template rendering errors
        return {}

    
def teacher_class_context(request):
    """Expose teacher classes and primary class to templates.

    Returns:
        dict: 'teacher_classes' (QuerySet) and 'teacher_primary_class' (ClassRoom or None)
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    teacher_classes = UserHierarchy.get_accessible_classes(user).select_related('grade', 'academic_year') if user.user_type == 'teacher' else None
    teacher_primary = None
    if teacher_classes:
        teacher_primary = teacher_classes.first()

    return {
        'teacher_classes': teacher_classes,
        'teacher_primary_class': teacher_primary,
    }
