from django.db import models
from django.utils import timezone
from administration.models import User
import uuid


class SyncLog(models.Model):
    """Track all synchronization operations"""
    SYNC_TYPE_CHOICES = (
        ('push', 'Push to Cloud'),
        ('pull', 'Pull from Cloud'),
        ('full', 'Full Sync'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    sync_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sync_type = models.CharField(max_length=10, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    records_pushed = models.IntegerField(default=0)
    records_pulled = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    device_id = models.CharField(max_length=100, help_text="Unique identifier for the device")
    
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['sync_id']),
            models.Index(fields=['device_id', 'started_at']),
        ]
    
    def __str__(self):
        sync_type_label = dict(self.SYNC_TYPE_CHOICES).get(self.sync_type, self.sync_type)
        return f"{sync_type_label} - {self.status} ({self.started_at})"


class PendingSync(models.Model):
    """Queue of changes waiting to be synced to cloud"""
    OPERATION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    )
    
    # What changed
    model_name = models.CharField(max_length=100, help_text="e.g., 'administration.Student'")
    record_id = models.CharField(max_length=100, help_text="Primary key of the record")
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    
    # When and where
    created_at = models.DateTimeField(default=timezone.now)
    device_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Data
    data = models.JSONField(help_text="Serialized record data")
    
    # Sync status
    is_synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    sync_attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    # Priority (for conflict resolution)
    priority = models.IntegerField(default=0, help_text="Higher priority wins conflicts")
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['is_synced', 'created_at']),
            models.Index(fields=['model_name', 'record_id']),
            models.Index(fields=['device_id']),
        ]
    
    def __str__(self):
        return f"{self.operation.upper()} {self.model_name}:{self.record_id}"


class SyncConflict(models.Model):
    """Track conflicts that need manual resolution"""
    RESOLUTION_CHOICES = (
        ('pending', 'Pending Resolution'),
        ('use_local', 'Use Local Version'),
        ('use_remote', 'Use Remote Version'),
        ('merge', 'Merge Both'),
        ('skip', 'Skip/Ignore'),
    )
    
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    
    # Conflicting versions
    local_data = models.JSONField(help_text="Local version data")
    remote_data = models.JSONField(help_text="Remote/cloud version data")
    
    local_timestamp = models.DateTimeField()
    remote_timestamp = models.DateTimeField()
    
    # Resolution
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, default='pending')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    detected_at = models.DateTimeField(default=timezone.now)
    device_id = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['resolution', 'detected_at']),
            models.Index(fields=['model_name', 'record_id']),
        ]
    
    def __str__(self):
        return f"Conflict: {self.model_name}:{self.record_id} ({self.resolution})"


class DeviceRegistration(models.Model):
    """Track registered devices for desktop app authentication"""
    device_id = models.CharField(max_length=100, unique=True)
    device_name = models.CharField(max_length=200, help_text="e.g., 'Principal Office PC'")
    
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_devices')
    registered_at = models.DateTimeField(default=timezone.now)
    
    last_sync_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Device info
    platform = models.CharField(max_length=50, blank=True, help_text="Windows, macOS, Linux")
    app_version = models.CharField(max_length=20, blank=True)
    
    # Access control
    allowed_users = models.ManyToManyField(User, related_name='allowed_devices', blank=True,
                                          help_text="Users who can use this device")
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-last_sync_at']
    
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"


class SyncSettings(models.Model):
    """Configuration for sync behavior"""
    SYNC_MODE_CHOICES = (
        ('auto', 'Automatic'),
        ('manual', 'Manual Only'),
        ('scheduled', 'Scheduled'),
    )
    
    device = models.OneToOneField(DeviceRegistration, on_delete=models.CASCADE, related_name='sync_settings')
    
    sync_mode = models.CharField(max_length=20, choices=SYNC_MODE_CHOICES, default='auto')
    sync_interval_minutes = models.IntegerField(default=15, help_text="For auto sync")
    
    # What to sync
    sync_on_startup = models.BooleanField(default=True)
    sync_on_shutdown = models.BooleanField(default=True)
    
    # Network settings
    require_wifi = models.BooleanField(default=False, help_text="Only sync on WiFi, not mobile data")
    retry_failed_syncs = models.BooleanField(default=True)
    max_retry_attempts = models.IntegerField(default=3)
    
    # Performance
    batch_size = models.IntegerField(default=100, help_text="Records per sync batch")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Sync Settings"
    
    def __str__(self):
        return f"Sync Settings for {self.device.device_name}"
