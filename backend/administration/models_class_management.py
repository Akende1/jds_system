"""
Extended models for class management features
Includes: ClassPromotion, StudentTransfer, TeacherAssignment, ClassStatistics
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from .models import Student, ClassRoom, User, AcademicYear, Term


class ClassPromotion(models.Model):
    """Track student promotions from one class to another"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotions')
    from_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='promoted_from')
    to_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='promoted_to')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='promotions')
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Performance criteria
    final_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                           help_text="Student's final percentage in previous class")
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                help_text="Student's attendance percentage")
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   limit_choices_to={'user_type__in': ['admin', 'head_teacher']},
                                   related_name='approved_promotions')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    promotion_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-promotion_date']
        unique_together = ['student', 'academic_year']  # One promotion per student per year
    
    def __str__(self):
        return f"{self.student} promoted from {self.from_class} to {self.to_class}"
    
    def approve(self, approved_by_user):
        """Approve the promotion and update student's class"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_date = timezone.now()
        self.save()
        
        # Update student's current class
        self.student.current_class = self.to_class
        self.student.save()
        
        self.status = 'completed'
        self.save()
    
    def reject(self, approved_by_user, reason=''):
        """Reject the promotion"""
        self.status = 'rejected'
        self.approved_by = approved_by_user
        self.approved_date = timezone.now()
        self.remarks = reason
        self.save()


class StudentTransfer(models.Model):
    """Track student transfers between classes (within same grade or different)"""
    
    TRANSFER_TYPE_CHOICES = (
        ('section', 'Section Transfer (Same Grade)'),
        ('grade', 'Grade Transfer'),
        ('disciplinary', 'Disciplinary Transfer'),
        ('request', 'Parent/Guardian Request'),
        ('academic', 'Academic Performance'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfers')
    from_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='transferred_from')
    to_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='transferred_to')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES)
    
    reason = models.TextField(help_text="Detailed reason for transfer")
    
    # Approval workflow
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    related_name='requested_transfers')
    requested_date = models.DateTimeField(default=timezone.now)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   limit_choices_to={'user_type__in': ['admin', 'head_teacher']},
                                   related_name='approved_transfers')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    transfer_date = models.DateTimeField(null=True, blank=True, help_text="Actual transfer execution date")
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_LABELS = {
        'requested': 'Requested',
        'approved': 'Approved',
        'rejected': 'Rejected',
        'completed': 'Completed',
    }
    
    class Meta:
        ordering = ['-transfer_date', '-requested_date']
    
    def __str__(self):
        return f"{self.student} - {self.from_class} -> {self.to_class} ({self.STATUS_LABELS.get(self.status, self.status)})"
    
    def approve_and_execute(self, approved_by_user):
        """Approve and execute the transfer"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_date = timezone.now()
        self.transfer_date = timezone.now()
        self.save()
        
        # Update student's current class
        self.student.current_class = self.to_class
        self.student.save()
        
        self.status = 'completed'
        self.save()


class TeacherAssignment(models.Model):
    """Assign teachers to classes for specific subjects"""
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, 
                               limit_choices_to={'user_type': 'teacher'},
                               related_name='teaching_assignments')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='teacher_assignments')
    
    # Subject assignment (if using subject model)
    subject_name = models.CharField(max_length=100, help_text="Subject being taught")
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True, related_name='teacher_assignments')
    
    # Workload details
    periods_per_week = models.IntegerField(default=0, help_text="Number of periods per week")
    
    # Assignment status
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['academic_year', 'classroom', 'subject_name']
        unique_together = ['teacher', 'classroom', 'subject_name', 'academic_year']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.subject_name} in {self.classroom}"


class ClassStatistics(models.Model):
    """Computed statistics for each class - updated periodically"""
    
    classroom = models.OneToOneField(ClassRoom, on_delete=models.CASCADE, related_name='statistics')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='class_statistics')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True, related_name='class_statistics')
    
    # Student demographics
    total_students = models.IntegerField(default=0)
    male_students = models.IntegerField(default=0)
    female_students = models.IntegerField(default=0)
    
    # Academic performance
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'),
                                            help_text="Average exam percentage")
    top_performer_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    lowest_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    
    # Attendance
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'),
                                                  help_text="Average attendance percentage")
    
    # Financial
    total_fees_expected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_fees_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    fee_collection_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'),
                                             help_text="Percentage of fees collected")
    
    # Last calculation
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['classroom']
        verbose_name_plural = 'Class Statistics'
    
    def __str__(self):
        return f"Statistics for {self.classroom}"
    
    @classmethod
    def calculate_for_class(cls, classroom, academic_year, term=None):
        """Calculate and save statistics for a class"""
        stats, created = cls.objects.get_or_create(
            classroom=classroom,
            academic_year=academic_year,
            term=term
        )
        
        # Get students in this class
        students = classroom.students.filter(is_active=True)
        stats.total_students = students.count()
        stats.male_students = students.filter(gender='M').count()
        stats.female_students = students.filter(gender='F').count()
        
        # Calculate attendance (if attendance module available)
        try:
            from attendance.models import StudentAttendance
            attendance_records = StudentAttendance.objects.filter(
                classroom=classroom,
                date__gte=academic_year.start_date,
                date__lte=academic_year.end_date
            )
            if term:
                attendance_records = attendance_records.filter(
                    date__gte=term.start_date,
                    date__lte=term.end_date
                )
            
            total_records = attendance_records.count()
            if total_records > 0:
                present_count = attendance_records.filter(status='present').count()
                stats.average_attendance_rate = (present_count / total_records) * 100
        except:
            pass
        
        # Calculate fees (if finance module available)
        try:
            from finance.models import FeeInvoice
            invoices = FeeInvoice.objects.filter(
                student__current_class=classroom,
                academic_year=academic_year
            )
            stats.total_fees_expected = sum(inv.total_amount for inv in invoices)
            stats.total_fees_collected = sum(inv.amount_paid for inv in invoices)
            
            if stats.total_fees_expected > 0:
                stats.fee_collection_rate = (stats.total_fees_collected / stats.total_fees_expected) * 100
        except:
            pass
        
        stats.save()
        return stats


class StudentSuspension(models.Model):
    """Formal student suspension records"""
    REASON_CHOICES = (
        ('behavior', 'Behavioral Issues'),
        ('attendance', 'Poor Attendance'),
        ('academic', 'Academic Fraud/Cheating'),
        ('violence', 'Violence/Aggression'),
        ('bullying', 'Bullying/Harassment'),
        ('drugs', 'Drug/Substance Use'),
        ('insubordination', 'Insubordination'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('requested', 'Suspension Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active/In Effect'),
        ('lifted', 'Lifted/Ended'),
        ('appealed', 'Under Appeal'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='suspensions')
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_student_suspensions',
                                    limit_choices_to={'user_type__in': ['head_teacher', 'manager', 'admin']})
    request_date = models.DateField(default=timezone.now)
    
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    detailed_reason = models.TextField()
    
    suspension_start_date = models.DateField()
    suspension_end_date = models.DateField()
    duration_days = models.IntegerField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_student_suspensions',
                                    limit_choices_to={'user_type__in': ['manager', 'admin']})
    approval_date = models.DateField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Parent notification
    parent_notified = models.BooleanField(default=False)
    parent_notification_date = models.DateField(null=True, blank=True)
    parent_response = models.TextField(blank=True)
    
    # Re-entry conditions
    reentry_conditions = models.TextField(blank=True, help_text="Conditions student must meet before returning")
    reentry_meeting_scheduled = models.BooleanField(default=False)
    reentry_meeting_date = models.DateField(null=True, blank=True)
    reentry_approved = models.BooleanField(default=False)
    
    # Appeal
    appealed = models.BooleanField(default=False)
    appeal_date = models.DateField(null=True, blank=True)
    appeal_reason = models.TextField(blank=True)
    appeal_decision = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-suspension_start_date']
        
    def __str__(self):
        return f"{self.student.full_name} - Suspension ({self.suspension_start_date})"


class StudentExpulsion(models.Model):
    """Formal student expulsion records"""
    REASON_CHOICES = (
        ('violence', 'Violence/Assault'),
        ('drugs', 'Drug Possession/Distribution'),
        ('weapons', 'Weapons/Dangerous Objects'),
        ('sexual', 'Sexual Misconduct'),
        ('repeated', 'Repeated Serious Violations'),
        ('academic', 'Academic Fraud/Cheating'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('recommended', 'Recommended for Expulsion'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('executed', 'Executed'),
        ('appealed', 'Under Appeal'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='expulsions')
    
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommended_expulsions',
                                       limit_choices_to={'user_type__in': ['head_teacher', 'manager', 'admin']})
    recommendation_date = models.DateField(default=timezone.now)
    
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    detailed_reason = models.TextField()
    incident_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recommended')
    
    # Investigation
    investigation_completed = models.BooleanField(default=False)
    investigation_notes = models.TextField(blank=True)
    witnesses = models.TextField(blank=True, help_text="List of witnesses/people involved")
    evidence = models.TextField(blank=True)
    
    # Approval by multiple levels
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_student_expulsions',
                                    limit_choices_to={'user_type__in': ['admin']})
    review_date = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_student_expulsions',
                                    limit_choices_to={'user_type__in': ['admin']})
    approval_date = models.DateField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Parent/Guardian communication
    parent_meeting_held = models.BooleanField(default=False)
    parent_meeting_date = models.DateField(null=True, blank=True)
    parent_meeting_notes = models.TextField(blank=True)
    
    parent_notified = models.BooleanField(default=False)
    parent_notification_date = models.DateField(null=True, blank=True)
    parent_response = models.TextField(blank=True)
    
    # Effective expulsion details
    expulsion_effective_date = models.DateField(null=True, blank=True)
    final_record_note = models.TextField(blank=True, help_text="Official note to be added to student record")
    
    # Appeal
    appealed = models.BooleanField(default=False)
    appeal_date = models.DateField(null=True, blank=True)
    appeal_reason = models.TextField(blank=True)
    appeal_decision = models.TextField(blank=True)
    
    # Transfer to alternative school
    transfer_to_school = models.CharField(max_length=200, blank=True)
    transfer_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-recommendation_date']
        
    def __str__(self):
        return f"{self.student.full_name} - Expulsion ({self.recommendation_date})"
