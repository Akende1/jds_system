from django.contrib import admin
from .models import UserRole, UserRoleAssignment, AuditLog, AccessLog, DataBackup, ComplianceDocument, SecurityIncident


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_by', 'assigned_on', 'is_active']
    list_filter = ['role', 'assigned_on', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'role__name']
    raw_id_fields = ['user', 'assigned_by']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'model_name', 'timestamp', 'ip_address']
    list_filter = ['action_type', 'model_name', 'timestamp']
    search_fields = ['user__first_name', 'model_name', 'ip_address']
    raw_id_fields = ['user']
    readonly_fields = ['timestamp']


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'ip_address']
    list_filter = ['login_time']
    search_fields = ['user__first_name', 'ip_address']
    raw_id_fields = ['user']


@admin.register(DataBackup)
class DataBackupAdmin(admin.ModelAdmin):
    list_display = ['backup_type', 'backup_date', 'file_size_mb', 'status']
    list_filter = ['status', 'backup_type', 'backup_date']
    search_fields = ['file_path']
    raw_id_fields = ['started_by']


@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'issue_date', 'expiry_date', 'is_active']
    list_filter = ['document_type', 'is_active', 'issue_date']
    search_fields = ['title', 'document_type']


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'incident_date', 'reported_by']
    list_filter = ['severity', 'status', 'incident_date']
    search_fields = ['title', 'reported_by__first_name']
    raw_id_fields = ['reported_by', 'assigned_to']
