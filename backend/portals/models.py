from django.db import models
from django.utils import timezone
from administration.models import User, Student


class StudentPortalAccess(models.Model):
    """Control student portal access"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='portal_access')
    is_active = models.BooleanField(default=True)
    
    can_view_results = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    can_view_fees = models.BooleanField(default=True)
    can_submit_assignments = models.BooleanField(default=True)
    can_access_lms = models.BooleanField(default=True)
    
    last_login = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Student Portal Access Controls'
        
    def __str__(self):
        return f"{self.student.full_name} - Portal Access"


class ParentPortalAccess(models.Model):
    """Control parent portal access"""
    parent = models.OneToOneField(User, on_delete=models.CASCADE, 
                                 limit_choices_to={'user_type': 'parent'},
                                 related_name='parent_portal_access')
    is_active = models.BooleanField(default=True)
    
    can_view_results = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    can_view_fees = models.BooleanField(default=True)
    can_communicate_teachers = models.BooleanField(default=True)
    can_view_announcements = models.BooleanField(default=True)
    
    last_login = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Parent Portal Access Controls'
        
    def __str__(self):
        return f"{self.parent.get_full_name()} - Parent Portal Access"


class PortalNotification(models.Model):
    """Notifications for portal users"""
    NOTIFICATION_TYPE_CHOICES = (
        ('result', 'Result Published'),
        ('fee', 'Fee Due'),
        ('attendance', 'Attendance Alert'),
        ('assignment', 'New Assignment'),
        ('announcement', 'Announcement'),
        ('message', 'New Message'),
        ('event', 'Event Reminder'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portal_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


class EventCalendar(models.Model):
    """School events calendar"""
    EVENT_TYPE_CHOICES = (
        ('holiday', 'Holiday'),
        ('exam', 'Examination'),
        ('meeting', 'Meeting'),
        ('sports', 'Sports Event'),
        ('cultural', 'Cultural Event'),
        ('workshop', 'Workshop'),
        ('parent_teacher', 'Parent-Teacher Meeting'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    location = models.CharField(max_length=200, blank=True)
    
    is_public = models.BooleanField(default=True, help_text="Visible to parents and students")

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_events')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
        
    def __str__(self):
        return f"{self.title} ({self.start_date})"


class PortalFeedback(models.Model):
    """Feedback from portal users"""
    FEEDBACK_TYPE_CHOICES = (
        ('suggestion', 'Suggestion'),
        ('complaint', 'Complaint'),
        ('issue', 'Technical Issue'),
        ('appreciation', 'Appreciation'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portal_feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='feedback_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Portal Feedback'
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.subject}"

