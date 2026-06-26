from django.contrib import admin
from .models import Announcement, Message, SMSLog, EmailLog, Newsletter


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'target_audience', 'posted_by', 'posted_at', 'is_active']
    list_filter = ['priority', 'target_audience', 'is_active', 'posted_at']
    search_fields = ['title', 'content']
    raw_id_fields = ['posted_by']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'sent_at', 'is_read']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['subject', 'sender__first_name', 'recipient__first_name']
    raw_id_fields = ['sender', 'recipient']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'phone_number', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['phone_number', 'recipient__first_name', 'message']
    raw_id_fields = ['recipient']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'email_address', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['email_address', 'subject', 'recipient__first_name']
    raw_id_fields = ['recipient']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'issue_number', 'published_at', 'is_published']
    list_filter = ['is_published', 'published_at']
    search_fields = ['title', 'issue_number']
