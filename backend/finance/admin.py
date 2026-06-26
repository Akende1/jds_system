from django.contrib import admin
from .models import (
    FeeStructure, FeeDiscount, FeeInvoice, FeeInvoiceItem, Payment, Expense, 
    FinancialReport, LunchPlan, StudentLunchSubscription, LunchAttendance, LunchMenu,
    MonthlyServiceInvoice, OfficialReceipt, PaymentReminder, ArrearsTracking,
    LateFee, StudentAccountStatement, StockItem, RestockingRequest, StockTransaction
)


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee_type', 'grade', 'amount', 'payment_frequency', 'is_active']
    list_filter = ['fee_type', 'payment_frequency', 'is_active', 'academic_year']
    search_fields = ['name', 'description']


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'total_amount', 'amount_paid', 'balance', 'issue_date', 'due_date']
    list_filter = ['issue_date', 'due_date', 'academic_year', 'term']
    search_fields = ['invoice_number', 'student__user__first_name', 'student__user__last_name', 'student__admission_number']
    readonly_fields = ['invoice_number', 'total_amount', 'balance']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_method', 'payment_date', 'invoice']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'transaction_reference']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'amount', 'expense_date', 'payment_method']
    list_filter = ['category', 'payment_method', 'expense_date']
    search_fields = ['title', 'description', 'vendor']


@admin.register(LunchPlan)
class LunchPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'monthly_fee', 'term_fee', 'is_active']
    list_filter = ['plan_type', 'is_active', 'academic_year']
    search_fields = ['name', 'description']


@admin.register(StudentLunchSubscription)
class StudentLunchSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['student', 'plan', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    raw_id_fields = ['student']


@admin.register(LunchAttendance)
class LunchAttendanceAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'date', 'took_lunch', 'remarks']
    list_filter = ['date', 'took_lunch']
    date_hierarchy = 'date'
    raw_id_fields = ['subscription']


@admin.register(LunchMenu)
class LunchMenuAdmin(admin.ModelAdmin):
    list_display = ['week_start_date', 'day_of_week', 'meal_type', 'is_published']
    list_filter = ['day_of_week', 'meal_type', 'is_published']
    date_hierarchy = 'week_start_date'


@admin.register(MonthlyServiceInvoice)
class MonthlyServiceInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'month', 'year', 'total_amount', 'balance', 'due_date']
    list_filter = ['month', 'year', 'is_auto_generated']
    search_fields = ['invoice_number', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['invoice_number', 'total_amount', 'balance']
    raw_id_fields = ['student']


@admin.register(OfficialReceipt)
class OfficialReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'total_amount', 'payment_method', 'payment_date', 'is_voided']
    list_filter = ['payment_method', 'payment_date', 'is_voided']
    search_fields = ['receipt_number', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['receipt_number', 'total_amount']
    raw_id_fields = ['student', 'issued_by']


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ['student', 'reminder_type', 'outstanding_amount', 'payment_deadline', 'status']
    list_filter = ['reminder_type', 'status', 'created_at']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    raw_id_fields = ['student']


@admin.register(ArrearsTracking)
class ArrearsTrackingAdmin(admin.ModelAdmin):
    list_display = ['student', 'total_outstanding', 'aging_category', 'days_overdue', 'is_blocked_from_exams']
    list_filter = ['aging_category', 'is_blocked_from_exams', 'snapshot_date']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    raw_id_fields = ['student']


@admin.register(LateFee)
class LateFeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'penalty_type', 'penalty_value', 'grace_period_days', 'is_active']
    list_filter = ['penalty_type', 'is_active', 'academic_year']


@admin.register(StudentAccountStatement)
class StudentAccountStatementAdmin(admin.ModelAdmin):
    list_display = ['statement_number', 'student', 'start_date', 'end_date', 'closing_balance', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['statement_number', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['statement_number']
    raw_id_fields = ['student']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'current_quantity', 'minimum_threshold', 'unit_cost', 'is_active']
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'category', 'supplier']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Item Info', {'fields': ('name', 'category', 'supplier')}),
        ('Stock Levels', {'fields': ('unit', 'current_quantity', 'minimum_threshold')}),
        ('Pricing', {'fields': ('unit_cost',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(RestockingRequest)
class RestockingRequestAdmin(admin.ModelAdmin):
    list_display = ['staff', 'stock_item', 'quantity_requested', 'status', 'estimated_cost', 'created_at']
    list_filter = ['status', 'created_at', 'stock_item__category']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'stock_item__name', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'estimated_cost']
    fieldsets = (
        ('Request Details', {'fields': ('staff', 'stock_item', 'quantity_requested', 'reason')}),
        ('Approval', {'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')}),
        ('Costing', {'fields': ('estimated_cost', 'actual_cost')}),
        ('Linked Expense', {'fields': ('expense',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Approve selected restocking requests"""
        from django.utils import timezone
        for req in queryset.filter(status='pending'):
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            self.message_user(request, f'Approved restocking request for {req.stock_item.name}')
    
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected restocking requests"""
        from django.utils import timezone
        for req in queryset.filter(status='pending'):
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            self.message_user(request, f'Rejected restocking request for {req.stock_item.name}')
    
    reject_requests.short_description = 'Reject selected requests'


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'transaction_type', 'quantity', 'transaction_date', 'recorded_by']
    list_filter = ['transaction_type', 'transaction_date', 'stock_item__category']
    search_fields = ['stock_item__name', 'notes', 'recorded_by__first_name']
    readonly_fields = ['transaction_date', 'created_at']
    date_hierarchy = 'transaction_date'
    fieldsets = (
        ('Transaction Info', {'fields': ('stock_item', 'transaction_type', 'quantity')}),
        ('References', {'fields': ('restocking_request', 'expense', 'recorded_by')}),
        ('Notes', {'fields': ('notes',)}),
        ('Timestamps', {'fields': ('transaction_date', 'created_at'), 'classes': ('collapse',)}),
    )


admin.register(FeeDiscount)
admin.site.register(FeeInvoiceItem)
admin.site.register(FinancialReport)
