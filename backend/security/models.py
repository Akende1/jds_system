from django.db import models
from django.utils import timezone
from administration.models import User


class UserRole(models.Model):
    """Custom roles and permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Module-level permissions
    can_manage_administration = models.BooleanField(default=False)
    can_manage_academics = models.BooleanField(default=False)
    can_manage_finance = models.BooleanField(default=False)
    can_manage_communication = models.BooleanField(default=False)
    can_manage_attendance = models.BooleanField(default=False)
    can_manage_lms = models.BooleanField(default=False)
    can_manage_hr = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    can_manage_transport = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class UserRoleAssignment(models.Model):
    """Assign roles to users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='user_assignments')
    
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='roles_assigned_by_me')
    assigned_on = models.DateTimeField(default=timezone.now)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role']
        ordering = ['user', 'role']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role.name}"


class AuditLog(models.Model):
    """System audit trail"""
    ACTION_TYPE_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('export', 'Export'),
        ('print', 'Print'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    
    module = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    
    description = models.TextField()
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'Anonymous'
        return f"{user_str} - {self.get_action_type_display()} - {self.module} ({self.timestamp})"


class AccessLog(models.Model):
    """Track user access to the system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-login_time']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.login_time}"


class DataBackup(models.Model):
    """Track database backups"""
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    backup_type = models.CharField(max_length=50, 
                                   choices=(('full', 'Full Backup'), 
                                          ('incremental', 'Incremental'),
                                          ('manual', 'Manual')))
    
    backup_date = models.DateTimeField(default=timezone.now)
    file_path = models.CharField(max_length=500)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-backup_date']
        
    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.backup_date} ({self.get_status_display()})"


class ComplianceDocument(models.Model):
    """Store compliance certificates and documents"""
    DOCUMENT_TYPE_CHOICES = (
        ('registration', 'School Registration'),
        ('license', 'Operating License'),
        ('safety', 'Safety Certificate'),
        ('health', 'Health Certificate'),
        ('tax', 'Tax Documents'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    )
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    document_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    issuing_authority = models.CharField(max_length=200)
    
    document_file = models.FileField(upload_to='compliance/')
    
    is_active = models.BooleanField(default=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
        
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"


class SecurityIncident(models.Model):
    """Security incidents and safeguarding issues"""
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    incident_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    incident_date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=200)
    
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_incidents_reported')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='security_incidents_assigned')
    
    actions_taken = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date']
        
    def __str__(self):
        return f"{self.incident_number} - {self.title} ({self.get_severity_display()})"

