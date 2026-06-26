from django.contrib import admin
from .models import StudentPortalAccess, ParentPortalAccess, PortalNotification, EventCalendar, PortalFeedback


@admin.register(StudentPortalAccess)
class StudentPortalAccessAdmin(admin.ModelAdmin):
    list_display = ['student', 'is_active', 'last_login']
    list_filter = ['is_active', 'last_login']
    search_fields = ['student__user__first_name', 'student__admission_number']
    raw_id_fields = ['student']


@admin.register(ParentPortalAccess)
class ParentPortalAccessAdmin(admin.ModelAdmin):
    list_display = ['parent', 'is_active', 'last_login']
    list_filter = ['is_active', 'last_login']
    search_fields = ['parent__first_name', 'parent__last_name']
    raw_id_fields = ['parent']


@admin.register(PortalNotification)
class PortalNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'user', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'user__first_name']
    raw_id_fields = ['user']


@admin.register(EventCalendar)
class EventCalendarAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_date', 'end_date', 'location', 'is_public']
    list_filter = ['event_type', 'is_public', 'start_date']
    search_fields = ['title', 'location']


@admin.register(PortalFeedback)
class PortalFeedbackAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'feedback_type', 'status', 'created_at']
    list_filter = ['feedback_type', 'status', 'created_at']
    search_fields = ['subject', 'user__first_name']
    raw_id_fields = ['user', 'responded_by']
