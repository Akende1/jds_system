from django.db import models
from django.utils import timezone
from administration.models import User, Student, Staff, ClassRoom, AcademicYear


class StudentAttendance(models.Model):
    """Daily attendance for students"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused Absence'),
        ('sick', 'Sick'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 limit_choices_to={'user_type__in': ['teacher', 'admin']})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.date} ({self.get_status_display()})"


class StaffAttendance(models.Model):
    """Daily attendance for staff"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('on_leave', 'On Leave'),
        ('half_day', 'Half Day'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    
    working_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 limit_choices_to={'user_type': 'admin'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['-date', 'staff']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} ({self.get_status_display()})"


class AttendanceSummary(models.Model):
    """Monthly attendance summary for students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_summaries')
    month = models.DateField()  # First day of the month
    
    total_school_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)
    
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'month']
        ordering = ['-month', 'student']
        verbose_name_plural = 'Attendance Summaries'
        
    def __str__(self):
        return f"{self.student.full_name} - {self.month.strftime('%B %Y')}"


class DisciplineIncident(models.Model):
    """Discipline and behavior incidents"""
    SEVERITY_CHOICES = (
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('severe', 'Severe'),
    )
    
    INCIDENT_TYPE_CHOICES = (
        ('late_arrival', 'Late Arrival'),
        ('uniform_violation', 'Uniform Violation'),
        ('disruptive_behavior', 'Disruptive Behavior'),
        ('fighting', 'Fighting'),
        ('bullying', 'Bullying'),
        ('cheating', 'Cheating'),
        ('disrespect', 'Disrespect to Authority'),
        ('vandalism', 'Vandalism'),
        ('other', 'Other'),
    )
    
    ACTION_TAKEN_CHOICES = (
        ('warning', 'Verbal Warning'),
        ('written_warning', 'Written Warning'),
        ('detention', 'Detention'),
        ('suspension', 'Suspension'),
        ('parent_meeting', 'Parent Meeting'),
        ('counseling', 'Counseling'),
        ('community_service', 'Community Service'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='discipline_incidents')
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    location = models.CharField(max_length=200)
    
    description = models.TextField()
    witness_details = models.TextField(blank=True)
    
    action_taken = models.CharField(max_length=30, choices=ACTION_TAKEN_CHOICES)
    action_details = models.TextField()
    
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discipline_reports')
    parents_informed = models.BooleanField(default=False)
    parent_response = models.TextField(blank=True)
    
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.get_incident_type_display()} ({self.date})"


class BehaviorLog(models.Model):
    """Positive and negative behavior tracking"""
    BEHAVIOR_TYPE_CHOICES = (
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behavior_logs')
    behavior_type = models.CharField(max_length=10, choices=BEHAVIOR_TYPE_CHOICES)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    points = models.IntegerField(default=0, help_text="Points awarded or deducted")
    
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.title} ({self.get_behavior_type_display()})"

