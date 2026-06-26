from django.db import models
from django.utils import timezone
from administration.models import Student, AcademicYear, Term, Grade, User


# ============================================
# ACCOUNTING FOUNDATION
# ============================================

class BankAccount(models.Model):
    """Track all school bank accounts"""
    ACCOUNT_TYPE_CHOICES = (
        ('current', 'Current Account'),
        ('savings', 'Savings Account'),
        ('operating', 'Operating Account'),
        ('escrow', 'Escrow Account'),
    )
    
    account_name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    bank_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, unique=True)
    routing_code = models.CharField(max_length=50, blank=True)
    
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    account_holder = models.CharField(max_length=200)
    account_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                       limit_choices_to={'user_type__in': ['admin', 'manager']})
    
    is_active = models.BooleanField(default=True)
    last_reconciled = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['bank_name', 'account_name']
        
    def __str__(self):
        return f"{self.account_name} ({self.account_number})"


class ChartOfAccounts(models.Model):
    """General ledger account chart"""
    ACCOUNT_TYPE_CHOICES = (
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    )
    
    account_code = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    
    description = models.TextField(blank=True)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='sub_accounts')
    
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['account_code']
        
    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class GeneralLedgerEntry(models.Model):
    """General ledger transactions"""
    ENTRY_TYPE_CHOICES = (
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    )
    
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_date = models.DateField(default=timezone.now)
    
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    description = models.CharField(max_length=300)
    reference_type = models.CharField(max_length=30, blank=True, 
                                     help_text="Invoice, Payment, Expense, etc.")
    reference_id = models.CharField(max_length=50, blank=True)
    
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-entry_date', '-created_at']
        
    def __str__(self):
        return f"{self.account.account_code} - {self.entry_type.upper()} {self.amount}"


# ============================================
# FEE MANAGEMENT
# ============================================


class FeeStructure(models.Model):
    """Fee structure for different grades"""
    FEE_TYPE_CHOICES = (
        ('tuition', 'Tuition Fee'),
        ('admission', 'Admission Fee'),
        ('examination', 'Examination Fee'),
        ('transport', 'Transport Fee'),
        ('lunch', 'Lunch Fee'),
        ('boarding', 'Boarding Fee'),
        ('pta', 'PTA Levy'),
        ('ict', 'ICT Levy'),
        ('uniform', 'Uniform'),
        ('library', 'Library Fee'),
        ('laboratory', 'Laboratory Fee'),
        ('sports', 'Sports Fee'),
        ('development', 'Development Fee'),
        ('other', 'Other Fee'),
    )
    
    PAYMENT_FREQUENCY_CHOICES = (
        ('one_time', 'One Time'),
        ('term', 'Per Term'),
        ('annual', 'Annual'),
        ('monthly', 'Monthly'),
    )
    
    name = models.CharField(max_length=200)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='fee_structures', 
                             null=True, blank=True, help_text="Leave blank for school-wide fees")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_frequency = models.CharField(max_length=20, choices=PAYMENT_FREQUENCY_CHOICES, default='term')
    
    is_compulsory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['grade', 'fee_type']
        
    def __str__(self):
        grade_str = f"{self.grade.name} - " if self.grade else "All Grades - "
        return f"{grade_str}{self.name} ({self.academic_year.name})"


class FeeDiscount(models.Model):
    """Discounts and scholarships"""
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.value}{'%' if self.discount_type == 'percentage' else ' NGN'})"


class FeeInvoice(models.Model):
    """Fee invoices for students"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_invoices')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.ForeignKey(FeeDiscount, on_delete=models.SET_NULL, 
                                        null=True, blank=True, related_name='invoices')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
        
    def __str__(self):
        return f"{self.invoice_number} - {self.student.full_name}"
    
    def save(self, *args, **kwargs):
        # Calculate balance
        self.balance = self.net_amount - self.amount_paid
        
        # Update status based on payment
        if self.amount_paid >= self.net_amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif timezone.now().date() > self.due_date:
            self.status = 'overdue'
        else:
            self.status = 'pending'
            
        super().save(*args, **kwargs)


class FeeInvoiceItem(models.Model):
    """Individual items in a fee invoice"""
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='items')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['invoice', 'fee_structure']
        
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"


class Payment(models.Model):
    """Fee payments made by students"""
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('online', 'Online Payment'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    receipt_number = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    payment_date = models.DateTimeField(default=timezone.now)
    
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Bank/Gateway transaction ID")
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    remarks = models.TextField(blank=True)
    
    received_by = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        
    def __str__(self):
        return f"{self.receipt_number} - {self.student.full_name} - NGN {self.amount}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update invoice amount_paid if payment is confirmed
        if self.payment_status == 'confirmed':
            if is_new:
                self.invoice.amount_paid += self.amount
            self.invoice.save()


# ============================================
# PAYMENT MANAGEMENT & RECEIPTS
# ============================================

class PaymentReceipt(models.Model):
    """Formal payment receipts for audit trail"""
    RECEIPT_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('cancelled', 'Cancelled'),
    )
    
    receipt_number = models.CharField(max_length=50, unique=True)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name='receipt')
    
    issued_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=RECEIPT_STATUS_CHOICES, default='issued')
    
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  limit_choices_to={'user_type__in': ['admin', 'manager']})
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issued_date']
        
    def __str__(self):
        return f"{self.receipt_number} - {self.payment.student.full_name}"


# ============================================
# EXPENSE & APPROVAL MANAGEMENT
# ============================================

class ExpenseApprovalLevel(models.Model):
    """Define approval levels for expenses"""
    APPROVER_TYPE_CHOICES = (
        ('head_teacher', 'Head Teacher'),
        ('manager', 'Finance Manager'),
        ('principal', 'Principal/Admin'),
    )
    
    level = models.IntegerField(unique=True)  # 1, 2, 3, etc.
    approver_role = models.CharField(max_length=30, choices=APPROVER_TYPE_CHOICES)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level']
        
    def __str__(self):
        return f"Level {self.level} - {self.approver_role} (NGN {self.min_amount}+)"


class ExpenseApprovalWorkflow(models.Model):
    """Track approval workflow for expenses"""
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved_level_1', 'Approved Level 1'),
        ('approved_level_2', 'Approved Level 2'),
        ('approved_level_3', 'Approved Level 3'),
        ('rejected', 'Rejected'),
        ('approved', 'Fully Approved'),
    )
    
    expense = models.OneToOneField('Expense', on_delete=models.CASCADE, related_name='approval_workflow')
    
    current_level = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-submitted_date']
        
    def __str__(self):
        return f"{self.expense.expense_number} - {self.get_status_display()}"


class ExpenseApproval(models.Model):
    """Individual approval records"""
    APPROVAL_DECISION_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned for Revision'),
    )
    
    workflow = models.ForeignKey(ExpenseApprovalWorkflow, on_delete=models.CASCADE, related_name='approvals')
    approval_level = models.ForeignKey(ExpenseApprovalLevel, on_delete=models.PROTECT)
    
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=20, choices=APPROVAL_DECISION_CHOICES, default='pending')
    
    comments = models.TextField(blank=True)
    
    approval_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['workflow', 'approval_level']
        unique_together = ['workflow', 'approval_level']
        
    def __str__(self):
        return f"{self.workflow.expense.expense_number} - Level {self.approval_level.level} ({self.get_decision_display()})"


class Expense(models.Model):
    """School expenses tracking"""
    EXPENSE_CATEGORY_CHOICES = (
        ('salary', 'Staff Salary'),
        ('utility', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies'),
        ('transport', 'Transport'),
        ('infrastructure', 'Infrastructure'),
        ('marketing', 'Marketing'),
        ('professional_services', 'Professional Services'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    expense_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=EXPENSE_CATEGORY_CHOICES)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES, blank=True)
    
    expense_date = models.DateField(default=timezone.now)
    payment_date = models.DateField(null=True, blank=True)
    
    vendor_name = models.CharField(max_length=200, blank=True)
    invoice_reference = models.CharField(max_length=100, blank=True)
    
    description = models.TextField()
    receipt = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='requested_expenses')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_expenses',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    
    chart_of_accounts = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date']
        
    def __str__(self):
        return f"{self.expense_number} - {self.title} (NGN {self.amount})"


class FinancialReport(models.Model):
    """Financial reports and summaries"""
    REPORT_TYPE_CHOICES = (
        ('income', 'Income Statement'),
        ('balance', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow'),
        ('fee_collection', 'Fee Collection Summary'),
        ('expense', 'Expense Report'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    summary = models.TextField(blank=True)
    report_file = models.FileField(upload_to='financial_reports/', null=True, blank=True)
    
    generated_by = models.CharField(max_length=200)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"


# ============================================
# BUDGETING & RECONCILIATION
# ============================================

class BudgetAllocation(models.Model):
    """Budget allocation for expense categories"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='budgets')
    
    category = models.CharField(max_length=30, choices=Expense.EXPENSE_CATEGORY_CHOICES)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    description = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_budgets',
                                   limit_choices_to={'user_type__in': ['admin', 'manager']})
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['academic_year', 'category']
        unique_together = ['academic_year', 'category']
        
    def __str__(self):
        return f"{self.academic_year.name} - {self.get_category_display()}: NGN {self.allocated_amount}"
    
    def update_spent(self):
        """Recalculate spent and remaining amounts"""
        self.spent_amount = Expense.objects.filter(
            category=self.category,
            payment_status='paid',
            expense_date__gte=self.academic_year.start_date,
            expense_date__lte=self.academic_year.end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        self.remaining_amount = self.allocated_amount - self.spent_amount
        self.save()


class BankReconciliation(models.Model):
    """Bank account reconciliation records"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('discrepancies', 'Has Discrepancies'),
    )
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='reconciliations')
    
    reconciliation_date = models.DateField()
    statement_start_date = models.DateField()
    statement_end_date = models.DateField()
    
    statement_opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    statement_closing_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    system_opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    system_closing_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     limit_choices_to={'user_type__in': ['admin', 'manager']})
    reconciliation_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        
    def __str__(self):
        return f"{self.bank_account.account_name} - {self.reconciliation_date}"
    
    def calculate_variance(self):
        """Calculate difference between bank and system balances"""
        self.variance = self.statement_closing_balance - self.system_closing_balance
        return self.variance


class BankStatement(models.Model):
    """Track bank statements for reconciliation"""
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processed', 'Processed'),
        ('reconciled', 'Reconciled'),
    )
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='statements')
    
    statement_date = models.DateField()
    statement_period_start = models.DateField()
    statement_period_end = models.DateField()
    
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    total_debits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    statement_file = models.FileField(upload_to='bank_statements/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-statement_date']
        
    def __str__(self):
        return f"{self.bank_account.account_name} - {self.statement_date}"


class BankTransaction(models.Model):
    """Individual bank statement transactions"""
    TRANSACTION_TYPE_CHOICES = (
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    )
    
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name='transactions')
    
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    reference = models.CharField(max_length=100, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    matched_transaction = models.CharField(max_length=50, blank=True, help_text="ID of matched system transaction")
    is_matched = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
        
    def __str__(self):
        return f"{self.statement.bank_account.account_name} - {self.transaction_date} - NGN {self.amount}"


class LunchPlan(models.Model):
    """Monthly lunch service plans"""
    PLAN_TYPE_CHOICES = (
        ('full_month', 'Full Month'),
        ('specific_days', 'Specific Days'),
        ('term_package', 'Term Package'),
    )
    
    name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    term_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - K{self.monthly_fee}/month"


class StudentLunchSubscription(models.Model):
    """Student enrollment in lunch program"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lunch_subscriptions')
    plan = models.ForeignKey(LunchPlan, on_delete=models.PROTECT)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    pause_start = models.DateField(null=True, blank=True, help_text="Date when service was paused")
    pause_end = models.DateField(null=True, blank=True, help_text="Date when service resumes")
    pause_reason = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.plan.name}"


class LunchAttendance(models.Model):
    """Daily lunch attendance tracking"""
    subscription = models.ForeignKey(StudentLunchSubscription, on_delete=models.CASCADE, 
                                    related_name='attendance_records')
    date = models.DateField()
    took_lunch = models.BooleanField(default=True)
    remarks = models.CharField(max_length=200, blank=True)
    
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['subscription', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.subscription.student.user.get_full_name()} - {self.date}"


class LunchMenu(models.Model):
    """Weekly/Monthly lunch menu"""
    MEAL_TYPE_CHOICES = (
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
    )
    
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    )
    
    week_start_date = models.DateField()
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='lunch')
    
    menu_description = models.TextField()
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['week_start_date', 'day_of_week', 'meal_type']
        ordering = ['week_start_date', 'day_of_week']
        
    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.menu_description[:50]}"


class MonthlyServiceInvoice(models.Model):
    """Automated monthly invoices for recurring services (lunch, transport)"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='monthly_invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    
    month = models.IntegerField(help_text="1-12")
    year = models.IntegerField()
    
    tuition_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    is_auto_generated = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: MS-YYYY-MM-XXXXX
            from django.db.models import Max
            last_invoice = MonthlyServiceInvoice.objects.filter(
                year=self.year, month=self.month
            ).aggregate(Max('id'))
            next_id = (last_invoice['id__max'] or 0) + 1
            self.invoice_number = f"MS-{self.year}-{self.month:02d}-{next_id:05d}"
        
        self.total_amount = (
            self.tuition_amount + self.transport_amount + 
            self.lunch_amount + self.other_fees
        )
        self.balance = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ['student', 'month', 'year']
        ordering = ['-year', '-month']
        
    def __str__(self):
        return f"{self.invoice_number} - {self.student.user.get_full_name()}"


class OfficialReceipt(models.Model):
    """Official payment receipts"""
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_deposit', 'Bank Deposit'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card', 'Debit/Credit Card'),
    )
    
    receipt_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='receipts')
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='official_receipt',
                                   null=True, blank=True)
    
    # Receipt items breakdown
    tuition_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    transaction_reference = models.CharField(max_length=200, blank=True)
    
    # Balance information
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    payment_date = models.DateField()
    issued_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='issued_receipts')
    
    is_voided = models.BooleanField(default=False)
    void_reason = models.TextField(blank=True)
    voided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='voided_receipts')
    voided_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number: RCP-YYYY-XXXXX
            from django.db.models import Max
            import datetime
            year = datetime.datetime.now().year
            last_receipt = OfficialReceipt.objects.filter(
                receipt_number__startswith=f"RCP-{year}"
            ).aggregate(Max('id'))
            next_id = (last_receipt['id__max'] or 0) + 1
            self.receipt_number = f"RCP-{year}-{next_id:06d}"
        
        self.total_amount = (
            self.tuition_paid + self.transport_paid + self.lunch_paid +
            self.exam_fees_paid + self.uniform_paid + self.other_paid
        )
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-payment_date']
        
    def __str__(self):
        return f"{self.receipt_number} - K{self.total_amount}"


class PaymentReminder(models.Model):
    """Automated payment reminder system"""
    REMINDER_TYPE_CHOICES = (
        ('soft', 'Soft Reminder'),
        ('final', 'Final Warning'),
        ('exam_blacklist', 'Examination Blacklist Notice'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payment_reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    
    outstanding_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Breakdown
    tuition_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    month = models.IntegerField(null=True, blank=True, help_text="For monthly billing")
    
    payment_deadline = models.DateField()
    
    letter_content = models.TextField(help_text="Auto-generated letter content")
    letter_pdf = models.FileField(upload_to='payment_reminders/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery tracking
    sent_via_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    sent_via_sms = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    
    sent_via_app = models.BooleanField(default=False)
    app_sent_at = models.DateTimeField(null=True, blank=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.student.user.get_full_name()}"


class ArrearsTracking(models.Model):
    """Outstanding balance tracking with aging analysis"""
    AGING_CATEGORY_CHOICES = (
        ('current', '0-30 days'),
        ('recent', '31-60 days'),
        ('overdue', '61-90 days'),
        ('critical', '90+ days'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='arrears')
    
    total_outstanding = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Breakdown by type
    tuition_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalties = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    oldest_unpaid_date = models.DateField()
    days_overdue = models.IntegerField(default=0)
    aging_category = models.CharField(max_length=20, choices=AGING_CATEGORY_CHOICES)
    
    last_payment_date = models.DateField(null=True, blank=True)
    last_reminder_sent = models.DateField(null=True, blank=True)
    
    is_blocked_from_exams = models.BooleanField(default=False)
    
    snapshot_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-total_outstanding']
        verbose_name_plural = 'Arrears tracking'
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - K{self.total_outstanding} ({self.aging_category})"


class LateFee(models.Model):
    """Late fee penalties configuration"""
    name = models.CharField(max_length=200)
    
    penalty_type = models.CharField(max_length=20, choices=(
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ))
    
    penalty_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    grace_period_days = models.IntegerField(default=7, 
                                           help_text="Days after due date before penalty applies")
    
    applies_to_fee_type = models.CharField(max_length=20, blank=True,
                                          help_text="Leave blank to apply to all fees")
    
    is_active = models.BooleanField(default=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.penalty_value}{'%' if self.penalty_type == 'percentage' else ''}"


class StudentAccountStatement(models.Model):
    """Generated account statements for students"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='account_statements')
    statement_number = models.CharField(max_length=50, unique=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_invoiced = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    statement_pdf = models.FileField(upload_to='statements/', null=True, blank=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.statement_number} - {self.student.user.get_full_name()}"
        
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"


# ============================================
# STOCK MANAGEMENT & RESTOCKING
# ============================================

class StockItem(models.Model):
    """Food items and supplies for cooking operations"""
    UNIT_CHOICES = (
        ('kg', 'Kilograms'),
        ('liters', 'Liters'),
        ('units', 'Units'),
        ('dozen', 'Dozen'),
        ('boxes', 'Boxes'),
        ('bags', 'Bags'),
    )
    
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    
    # Stock tracking
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text="Trigger point for restocking requests")
    
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Categorization
    category = models.CharField(max_length=100, default='Kitchen Supplies')
    supplier = models.CharField(max_length=200, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.unit})"
    
    @property
    def needs_restocking(self):
        """Check if stock is below minimum threshold"""
        return self.current_quantity <= self.minimum_threshold


class RestockingRequest(models.Model):
    """Cooking staff request for items, requires manager approval"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('purchased', 'Purchased'),
        ('received', 'Received'),
    )
    
    staff = models.ForeignKey('administration.Staff', on_delete=models.CASCADE, 
                             related_name='restocking_requests')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, 
                                   related_name='restocking_requests')
    
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(help_text="Why is restocking needed?")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_restocking_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Purchase tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Link to expense if purchased
    expense = models.OneToOneField(Expense, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='restocking_request')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.stock_item.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate estimated cost (ensure Decimal multiplication)
        if not self.estimated_cost and self.stock_item:
            from decimal import Decimal
            quantity = Decimal(str(self.quantity_requested))
            unit_cost = Decimal(str(self.stock_item.unit_cost))
            self.estimated_cost = quantity * unit_cost
        super().save(*args, **kwargs)


class StockTransaction(models.Model):
    """Log all stock movements (purchases, usage, adjustments)"""
    TRANSACTION_TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('usage', 'Usage'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
        ('damage', 'Damage/Loss'),
    )
    
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, 
                                  related_name='transactions')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # For purchases: link to restocking request or expense
    restocking_request = models.ForeignKey(RestockingRequest, on_delete=models.SET_NULL, 
                                          null=True, blank=True)
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For usage: who used it
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    transaction_date = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        
    def __str__(self):
        return f"{self.stock_item.name} - {self.get_transaction_type_display()} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update stock quantity based on transaction
        if self.transaction_type in ['purchase', 'transfer']:
            self.stock_item.current_quantity += self.quantity
        elif self.transaction_type in ['usage', 'damage']:
            self.stock_item.current_quantity -= self.quantity
        
        self.stock_item.save()

