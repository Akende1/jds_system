from django.db import models
from django.utils import timezone
from administration.models import User, AcademicYear, Term, Grade, ClassRoom
from .models_schedule import ReportSchedule, ReportLog


class PerformanceTrend(models.Model):
    """Track academic performance trends"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True)
    
    total_students = models.IntegerField(default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    students_above_90 = models.IntegerField(default=0)
    students_above_80 = models.IntegerField(default=0)
    students_above_70 = models.IntegerField(default=0)
    students_above_60 = models.IntegerField(default=0)
    students_above_50 = models.IntegerField(default=0)
    students_below_50 = models.IntegerField(default=0)
    
    pass_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-academic_year', '-term']
        
    def __str__(self):
        level_str = f"{self.classroom}" if self.classroom else f"{self.grade}" if self.grade else "School-wide"
        return f"Performance Trend - {level_str} ({self.term})"


class AttendanceTrend(models.Model):
    """Track attendance trends"""
    month = models.DateField()  # First day of the month
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True)
    
    total_students = models.IntegerField(default=0)
    total_school_days = models.IntegerField(default=0)
    
    average_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)
    total_late = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        
    def __str__(self):
        level_str = f"{self.classroom}" if self.classroom else f"{self.grade}" if self.grade else "School-wide"
        return f"Attendance Trend - {level_str} ({self.month.strftime('%B %Y')})"


class FinancialDashboard(models.Model):
    """Financial analytics dashboard"""
    month = models.DateField()  # First day of the month
    
    total_fee_expected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_fee_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_fee_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    collection_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    number_of_defaulters = models.IntegerField(default=0)
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        
    def __str__(self):
        return f"Financial Dashboard - {self.month.strftime('%B %Y')}"


class EnrollmentPattern(models.Model):
    """Enrollment analytics"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    month = models.DateField()
    
    total_students = models.IntegerField(default=0)
    new_admissions = models.IntegerField(default=0)
    withdrawals = models.IntegerField(default=0)
    
    male_students = models.IntegerField(default=0)
    female_students = models.IntegerField(default=0)
    
    # By grade distribution
    grade_wise_data = models.JSONField(default=dict, blank=True)
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-academic_year', '-month']
        
    def __str__(self):
        return f"Enrollment - {self.academic_year.name} ({self.month.strftime('%B %Y')})"


class TeacherWorkload(models.Model):
    """Analyze teacher workload"""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE,
                               limit_choices_to={'user_type': 'teacher'},
                               related_name='workload_analytics')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    
    total_classes = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    total_periods_per_week = models.IntegerField(default=0)
    
    subjects_taught = models.IntegerField(default=0)
    is_class_teacher = models.BooleanField(default=False)
    
    assignments_created = models.IntegerField(default=0)
    assignments_graded = models.IntegerField(default=0)
    
    workload_score = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                         help_text="Calculated workload index")
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['teacher', 'academic_year', 'term']
        ordering = ['-workload_score']
        
    def __str__(self):
        return f"{self.teacher.get_full_name()} - Workload ({self.term})"


class DisciplineAnalytics(models.Model):
    """Discipline incidents analytics"""
    month = models.DateField()
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)
    
    total_incidents = models.IntegerField(default=0)
    minor_incidents = models.IntegerField(default=0)
    moderate_incidents = models.IntegerField(default=0)
    major_incidents = models.IntegerField(default=0)
    severe_incidents = models.IntegerField(default=0)
    
    # By incident type
    incident_type_distribution = models.JSONField(default=dict, blank=True)
    
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        verbose_name_plural = 'Discipline Analytics'
        
    def __str__(self):
        grade_str = f"{self.grade.name}" if self.grade else "School-wide"
        return f"Discipline Analytics - {grade_str} ({self.month.strftime('%B %Y')})"


class CustomReport(models.Model):
    """Custom reports created by users"""
    REPORT_TYPE_CHOICES = (
        ('academic', 'Academic Report'),
        ('financial', 'Financial Report'),
        ('attendance', 'Attendance Report'),
        ('discipline', 'Discipline Report'),
        ('hr', 'HR Report'),
        ('inventory', 'Inventory Report'),
        ('transport', 'Transport Report'),
        ('custom', 'Custom Report'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField()
    
    parameters = models.JSONField(default=dict, help_text="Report parameters and filters")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_reports')
    
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True,
                                         choices=(('daily', 'Daily'), 
                                                ('weekly', 'Weekly'),
                                                ('monthly', 'Monthly')))
    
    last_generated = models.DateTimeField(null=True, blank=True)
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

