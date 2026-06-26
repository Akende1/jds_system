from django.db import models
from django.utils import timezone
from administration.models import Staff, User


class LeaveType(models.Model):
    """Types of leave available"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    max_days_per_year = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class LeaveApplication(models.Model):
    """Leave applications by staff"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(default=1)
    
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    applied_on = models.DateTimeField(default=timezone.now)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='leave_approvals')
    approved_on = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(blank=True)
    
    attachment = models.FileField(upload_to='leave_documents/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_on']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"


class PayrollStructure(models.Model):
    """Salary structure components"""
    COMPONENT_TYPE_CHOICES = (
        ('earning', 'Earning'),
        ('deduction', 'Deduction'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPE_CHOICES)
    
    is_percentage = models.BooleanField(default=False)
    default_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['component_type', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"


class Payroll(models.Model):
    """Monthly payroll for staff"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField()  # First day of the month
    
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_on_leave = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'month']
        ordering = ['-month', 'staff']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.month.strftime('%B %Y')}"


class PayrollComponent(models.Model):
    """Individual components of a payroll"""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='components')
    structure_component = models.ForeignKey(PayrollStructure, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['payroll', 'structure_component']
        
    def __str__(self):
        return f"{self.payroll} - {self.structure_component.name}: {self.amount}"


# ============================================
# ALLOWANCES & DEDUCTIONS
# ============================================

class StaffAllowance(models.Model):
    """Individual staff allowances (Housing, Transport, Medical, etc.)"""
    ALLOWANCE_TYPE_CHOICES = (
        ('housing', 'Housing Allowance'),
        ('transport', 'Transport Allowance'),
        ('medical', 'Medical Allowance'),
        ('meal', 'Meal Allowance'),
        ('hardship', 'Hardship Allowance'),
        ('performance', 'Performance Bonus'),
        ('responsibility', 'Responsibility Allowance'),
        ('other', 'Other Allowance'),
    )
    
    FREQUENCY_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('one_time', 'One Time'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('ended', 'Ended'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='allowances')
    
    allowance_type = models.CharField(max_length=30, choices=ALLOWANCE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    reason = models.TextField(blank=True, help_text="Reason for the allowance")
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_allowances',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    approval_date = models.DateField(null=True, blank=True)
    
    is_taxable = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_allowance_type_display()} (NGN {self.amount})"
    
    def is_active(self):
        """Check if allowance is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.status == 'active' and self.start_date <= today and (self.end_date is None or today <= self.end_date)


class StaffDeduction(models.Model):
    """Individual staff deductions (Tax, Pension, Loan, etc.)"""
    DEDUCTION_TYPE_CHOICES = (
        ('income_tax', 'Income Tax'),
        ('pension', 'Pension Contribution'),
        ('health_insurance', 'Health Insurance'),
        ('loan', 'Loan Repayment'),
        ('salary_advance', 'Salary Advance Recovery'),
        ('disciplinary', 'Disciplinary Fine'),
        ('other', 'Other Deduction'),
    )
    
    FREQUENCY_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('one_time', 'One Time'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('ended', 'Ended'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='deductions')
    
    deduction_type = models.CharField(max_length=30, choices=DEDUCTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    reason = models.TextField(blank=True, help_text="Reason for the deduction")
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_deductions',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    approval_date = models.DateField(null=True, blank=True)
    
    # For variable deductions
    is_fixed = models.BooleanField(default=True)
    percentage_of_salary = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                              help_text="If percentage-based")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_deduction_type_display()} (NGN {self.amount})"
    
    def is_active(self):
        """Check if deduction is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.status == 'active' and self.start_date <= today and (self.end_date is None or today <= self.end_date)


# ============================================
# PAYSLIPS
# ============================================

class PaySlip(models.Model):
    """Formal payslip document for employee payment"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('signed', 'Signed by Employee'),
        ('voided', 'Voided'),
    )
    
    payroll = models.OneToOneField(Payroll, on_delete=models.PROTECT, related_name='payslip')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='payslips')
    
    payslip_number = models.CharField(max_length=50, unique=True)
    payslip_period_start = models.DateField()
    payslip_period_end = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Basic Info
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Earnings
    total_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Net
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Attendance
    working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_on_leave = models.IntegerField(default=0)
    
    # Approval
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='generated_payslips')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_payslips',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    approval_date = models.DateField(null=True, blank=True)
    
    # Employee acknowledgment
    employee_acknowledged = models.BooleanField(default=False)
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    
    # Remarks
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payslip_period_end']
        
    def __str__(self):
        return f"{self.payslip_number} - {self.staff.user.get_full_name()} ({self.payslip_period_start})"
    
    def save(self, *args, **kwargs):
        """Calculate totals on save"""
        self.gross_salary = self.basic_salary + self.total_allowances
        self.net_salary = self.gross_salary - self.total_deductions
        super().save(*args, **kwargs)


class PaySlipAllowance(models.Model):
    """Allowances included in a payslip"""
    payslip = models.ForeignKey(PaySlip, on_delete=models.CASCADE, related_name='allowance_items')
    allowance = models.ForeignKey(StaffAllowance, on_delete=models.PROTECT)
    
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['payslip']
        
    def __str__(self):
        return f"{self.payslip.payslip_number} - {self.description}: NGN {self.amount}"


class PaySlipDeduction(models.Model):
    """Deductions included in a payslip"""
    payslip = models.ForeignKey(PaySlip, on_delete=models.CASCADE, related_name='deduction_items')
    deduction = models.ForeignKey(StaffDeduction, on_delete=models.PROTECT)
    
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['payslip']
        
    def __str__(self):
        return f"{self.payslip.payslip_number} - {self.description}: NGN {self.amount}"


class PayslipBatch(models.Model):
    """Batch processing of multiple payslips"""
    BATCH_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
    )
    
    batch_number = models.CharField(max_length=50, unique=True)
    batch_period_start = models.DateField()
    batch_period_end = models.DateField()
    
    total_staff = models.IntegerField(default=0)
    payslips_generated = models.IntegerField(default=0)
    
    total_gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='pending')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='created_payslip_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_payslip_batches',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    approval_date = models.DateTimeField(null=True, blank=True)
    
    payment_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-batch_period_start']
        
    def __str__(self):
        return f"{self.batch_number} ({self.batch_period_start} to {self.batch_period_end})"


class Contract(models.Model):
    """Employment contracts"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='contracts')
    contract_number = models.CharField(max_length=50, unique=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    contract_type = models.CharField(max_length=20, 
                                    choices=(('permanent', 'Permanent'), 
                                           ('temporary', 'Temporary'),
                                           ('contract', 'Contract')),
                                    default='permanent')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    terms_and_conditions = models.TextField()
    contract_document = models.FileField(upload_to='contracts/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.contract_number}"


class PerformanceReview(models.Model):
    """Staff performance evaluations"""
    RATING_CHOICES = (
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='performance_reviews')
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    
    reviewed_by = models.ForeignKey(User, on_delete=models.CASCADE, 
                                   limit_choices_to={'user_type__in': ['manager', 'head_teacher']})
    review_date = models.DateField(default=timezone.now)
    
    # Performance metrics
    punctuality_rating = models.IntegerField(choices=RATING_CHOICES)
    work_quality_rating = models.IntegerField(choices=RATING_CHOICES)
    communication_rating = models.IntegerField(choices=RATING_CHOICES)
    teamwork_rating = models.IntegerField(choices=RATING_CHOICES)
    initiative_rating = models.IntegerField(choices=RATING_CHOICES)
    
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    goals_for_next_period = models.TextField()
    
    staff_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-review_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - Review {self.review_date}"
    
    def save(self, *args, **kwargs):
        # Calculate overall rating
        ratings = [
            self.punctuality_rating,
            self.work_quality_rating,
            self.communication_rating,
            self.teamwork_rating,
            self.initiative_rating,
        ]
        self.overall_rating = sum(ratings) / len(ratings)
        super().save(*args, **kwargs)


class Training(models.Model):
    """Staff training and development programs"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    trainer_name = models.CharField(max_length=200)
    venue = models.CharField(max_length=200)
    
    start_date = models.DateField()
    end_date = models.DateField()
    duration_hours = models.IntegerField(default=0)
    
    max_participants = models.IntegerField(default=50)
    cost_per_participant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_mandatory = models.BooleanField(default=False)
    certificate_provided = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.title} ({self.start_date})"


class TrainingAttendance(models.Model):
    """Track staff attendance in training programs"""
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='attendances')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='training_attendances')
    
    attended = models.BooleanField(default=False)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    feedback = models.TextField(blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['training', 'staff']
        ordering = ['training', 'staff']
        verbose_name_plural = 'Training Attendances'
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.training.title}"


class StaffDisciplinaryAction(models.Model):
    """Record formal disciplinary actions taken against staff"""
    ACTION_TYPE_CHOICES = (
        ('warning', 'Verbal Warning'),
        ('written_warning', 'Written Warning'),
        ('suspension', 'Suspension'),
        ('demotion', 'Demotion'),
        ('termination', 'Termination'),
        ('fine', 'Fine'),
        ('other', 'Other'),
    )
    
    SEVERITY_CHOICES = (
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('severe', 'Severe'),
    )
    
    STATUS_CHOICES = (
        ('reported', 'Reported'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('appealed', 'Appealed'),
        ('resolved', 'Resolved'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='disciplinary_actions')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_disciplinary_reports')
    
    incident_date = models.DateField()
    incident_description = models.TextField()
    evidence = models.TextField(blank=True, help_text="Document the evidence/details supporting the action")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    # Review and approval
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='staff_disciplinary_reviews',
                                    limit_choices_to={'user_type__in': ['manager', 'admin']})
    review_date = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Implementation
    implemented = models.BooleanField(default=False)
    implementation_date = models.DateField(null=True, blank=True)
    implementation_notes = models.TextField(blank=True)
    
    # Appeal
    appealed = models.BooleanField(default=False)
    appeal_date = models.DateField(null=True, blank=True)
    appeal_reason = models.TextField(blank=True)
    appeal_decision = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incident_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_action_type_display()} ({self.incident_date})"


class StaffSuspensionRequest(models.Model):
    """Formal suspension requests for staff members"""
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='suspension_requests')
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_suspension_requests',
                                    limit_choices_to={'user_type__in': ['manager', 'admin', 'head_teacher']})
    request_date = models.DateField(default=timezone.now)
    
    reason = models.TextField()
    suspension_start_date = models.DateField()
    suspension_end_date = models.DateField()
    duration_days = models.IntegerField()
    
    # Conditions during suspension
    pay_during_suspension = models.BooleanField(default=True)
    benefits_during_suspension = models.BooleanField(default=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Review and approval
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='staff_suspension_approvals',
                                    limit_choices_to={'user_type__in': ['manager', 'admin']})
    review_date = models.DateField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    
    staff_acknowledgement = models.BooleanField(default=False)
    acknowledgement_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - Suspension ({self.suspension_start_date})"


class StaffTerminationRequest(models.Model):
    """Formal termination/dismissal requests for staff members"""
    REASON_CHOICES = (
        ('performance', 'Poor Performance'),
        ('conduct', 'Misconduct'),
        ('redundancy', 'Redundancy'),
        ('contract_end', 'Contract End'),
        ('resignation', 'Resignation'),
        ('retirement', 'Retirement'),
        ('health', 'Health Issues'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
        ('withdrawn', 'Withdrawn'),
    )
    
    SEVERANCE_TYPE_CHOICES = (
        ('full', 'Full Severance'),
        ('partial', 'Partial Severance'),
        ('none', 'No Severance'),
    )
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='termination_requests')
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_termination_requests',
                                    limit_choices_to={'user_type__in': ['manager', 'admin']})
    request_date = models.DateField(default=timezone.now)
    
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    detailed_reason = models.TextField()
    
    effective_date = models.DateField()
    notice_period_days = models.IntegerField(default=30)
    
    # Severance
    severance_type = models.CharField(max_length=20, choices=SEVERANCE_TYPE_CHOICES, default='full')
    severance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Leave clearance
    outstanding_leave_days = models.IntegerField(default=0)
    outstanding_leave_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Review and approval
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='staff_termination_approvals',
                                    limit_choices_to={'user_type__in': ['manager', 'admin']})
    review_date = models.DateField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    
    staff_acknowledgement = models.BooleanField(default=False)
    acknowledgement_date = models.DateField(null=True, blank=True)
    
    # Exit documentation
    exit_interview_completed = models.BooleanField(default=False)
    exit_interview_date = models.DateField(null=True, blank=True)
    exit_interview_notes = models.TextField(blank=True)
    
    assets_returned = models.BooleanField(default=False)
    final_settlement_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - Termination ({self.request_date})"

