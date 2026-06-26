from django.contrib import admin
from .models import SyncLog, PendingSync, SyncConflict, DeviceRegistration, SyncSettings


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_id', 'sync_type', 'status', 'started_at', 'records_pushed', 'records_pulled', 'device_id']
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['sync_id', 'device_id', 'error_message']
    readonly_fields = ['sync_id', 'started_at', 'completed_at']
    raw_id_fields = ['initiated_by']


@admin.register(PendingSync)
class PendingSyncAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'record_id', 'operation', 'created_at', 'is_synced', 'sync_attempts', 'device_id']
    list_filter = ['is_synced', 'operation', 'model_name', 'created_at']
    search_fields = ['model_name', 'record_id', 'device_id']
    readonly_fields = ['created_at', 'synced_at']
    raw_id_fields = ['user']


@admin.register(SyncConflict)
class SyncConflictAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'record_id', 'resolution', 'detected_at', 'resolved_at', 'device_id']
    list_filter = ['resolution', 'detected_at', 'model_name']
    search_fields = ['model_name', 'record_id', 'device_id']
    readonly_fields = ['detected_at', 'resolved_at']
    raw_id_fields = ['resolved_by']


@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'device_id', 'platform', 'is_active', 'last_sync_at', 'registered_at']
    list_filter = ['is_active', 'platform', 'registered_at']
    search_fields = ['device_name', 'device_id']
    filter_horizontal = ['allowed_users']
    raw_id_fields = ['registered_by']


@admin.register(SyncSettings)
class SyncSettingsAdmin(admin.ModelAdmin):
    list_display = ['device', 'sync_mode', 'sync_interval_minutes', 'sync_on_startup', 'updated_at']
    list_filter = ['sync_mode', 'sync_on_startup']
    search_fields = ['device__device_name']
