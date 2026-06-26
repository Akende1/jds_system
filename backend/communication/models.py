from django.db import models
from django.utils import timezone
from administration.models import User, Student, ClassRoom


class Announcement(models.Model):
    """School-wide announcements"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    TARGET_AUDIENCE_CHOICES = (
        ('all', 'Everyone'),
        ('students', 'Students Only'),
        ('parents', 'Parents Only'),
        ('staff', 'Staff Only'),
        ('teachers', 'Teachers Only'),
        ('specific_class', 'Specific Class'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='all')
    target_classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True,
                                        help_text="Required if target is specific class")
    
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements_created')
    posted_at = models.DateTimeField(default=timezone.now)

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_announcements')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"


class Message(models.Model):
    """Direct messages between users"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_received')
    
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    attachment = models.FileField(upload_to='messages/', null=True, blank=True)

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_messages')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    sent_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-sent_at']
        
    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.subject}"


class Newsletter(models.Model):
    """School newsletters"""
    title = models.CharField(max_length=200)
    issue_number = models.CharField(max_length=50)
    content = models.TextField()
    
    cover_image = models.ImageField(upload_to='newsletters/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='newsletters/pdf/', null=True, blank=True)
    
    published_by = models.ForeignKey(User, on_delete=models.CASCADE)
    published_at = models.DateTimeField(default=timezone.now)
    
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_at']
        
    def __str__(self):
        return f"{self.title} - Issue {self.issue_number}"


class SMSLog(models.Model):
    """SMS communication log"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_received')
    phone_number = models.CharField(max_length=17)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    gateway_response = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'
        
    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"


class EmailLog(models.Model):
    """Email communication log"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails_received')
    email_address = models.EmailField()
    
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Email to {self.email_address} - {self.subject}"


class ParentTeacherCommunication(models.Model):
    """Parent-teacher communication records"""
    COMMUNICATION_TYPE_CHOICES = (
        ('meeting', 'Meeting'),
        ('phone_call', 'Phone Call'),
        ('email', 'Email'),
        ('note', 'Written Note'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parent_teacher_communications')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, 
                               limit_choices_to={'user_type': 'teacher'},
                               related_name='parent_communications')
    parent = models.ForeignKey(User, on_delete=models.CASCADE,
                              limit_choices_to={'user_type': 'parent'},
                              related_name='teacher_communications')
    
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    details = models.TextField()
    
    communication_date = models.DateTimeField(default=timezone.now)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-communication_date']
        
    def __str__(self):
        return f"{self.teacher} - {self.parent} about {self.student.full_name}"


class AppointmentRequest(models.Model):
    """Meeting / appointment requests."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rescheduled', 'Rescheduled'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    )

    MEETING_WITH_CHOICES = (
        ('teacher', 'Teacher'),
        ('management', 'Management'),
        ('both', 'Teacher and Management'),
    )

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointment_requests')
    meeting_with = models.CharField(max_length=20, choices=MEETING_WITH_CHOICES, default='teacher')
    specific_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       limit_choices_to={'user_type__in': ['teacher', 'manager', 'head_teacher']},
                                       related_name='appointment_target_requests')
    subject = models.CharField(max_length=200)
    details = models.TextField()

    preferred_date = models.DateField()
    preferred_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    location = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    staff_response = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='appointment_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requested_by.get_full_name()} - {self.subject}"

