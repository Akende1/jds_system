from django.db import models
from django.utils import timezone
from administration.models import User


class ReportSchedule(models.Model):
    """Schedule automated report generation and delivery"""
    
    REPORT_TYPE_CHOICES = (
        ('student_list', 'Student List'),
        ('fee_summary', 'Fee Summary Report'),
        ('attendance_summary', 'Attendance Summary'),
        ('performance_report', 'Academic Performance Report'),
        ('comprehensive', 'Comprehensive School Report'),
    )
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    FORMAT_CHOICES = (
        ('excel', 'Excel Spreadsheet'),
        ('pdf', 'PDF Document'),
        ('both', 'Both Excel and PDF'),
    )
    
    name = models.CharField(max_length=200, help_text="Descriptive name for this scheduled report")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='excel')
    
    # Email configuration
    recipients = models.TextField(help_text="Comma-separated email addresses")
    email_subject = models.CharField(max_length=200, blank=True)
    email_body = models.TextField(blank=True, help_text="Custom message to include in email")
    
    # Filters (JSON for flexibility)
    filter_grade = models.CharField(max_length=50, blank=True, help_text="Filter by specific grade")
    filter_class = models.CharField(max_length=50, blank=True, help_text="Filter by specific class")
    filter_date_from = models.DateField(null=True, blank=True, help_text="Start date for date-range reports")
    filter_date_to = models.DateField(null=True, blank=True, help_text="End date for date-range reports")
    
    # Scheduling
    is_active = models.BooleanField(default=True)
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        frequency_labels = dict(self.FREQUENCY_CHOICES)
        return f"{self.name} ({frequency_labels.get(self.frequency, self.frequency)})"
    
    def get_recipient_list(self):
        """Parse comma-separated recipients into list"""
        return [email.strip() for email in self.recipients.split(',') if email.strip()]
    
    def calculate_next_run(self):
        """Calculate next scheduled run time based on frequency"""
        from datetime import timedelta
        
        now = timezone.now()
        
        if self.frequency == 'daily':
            self.next_run = now + timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_run = now + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # Next month, same day
            next_month = now.month + 1 if now.month < 12 else 1
            next_year = now.year if now.month < 12 else now.year + 1
            self.next_run = now.replace(year=next_year, month=next_month)
        elif self.frequency == 'quarterly':
            self.next_run = now + timedelta(days=90)
        elif self.frequency == 'yearly':
            self.next_run = now.replace(year=now.year + 1)
        
        self.save()


class ReportLog(models.Model):
    """Log of generated reports"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('sent', 'Sent via Email'),
    )
    
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    report_type = models.CharField(max_length=50)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    
    # Email delivery
    recipients = models.TextField(blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_file_size_display(self):
        """Human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.2f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.2f} MB"
