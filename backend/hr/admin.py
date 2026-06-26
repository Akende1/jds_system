from django.contrib import admin
from .models import (
    LeaveType, LeaveApplication, PayrollStructure, Payroll, PayrollComponent,
    PerformanceReview, Training, TrainingAttendance, StaffDisciplinaryAction,
    StaffSuspensionRequest, StaffTerminationRequest, StaffAllowance, StaffDeduction,
    PaySlip, PaySlipAllowance, PaySlipDeduction, PayslipBatch
)


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_days_per_year', 'is_paid', 'is_active']
    list_filter = ['is_paid', 'is_active']
    search_fields = ['name', 'code']


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['staff', 'leave_type', 'start_date', 'end_date', 'total_days', 'status']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'approved_by']


@admin.register(PayrollStructure)
class PayrollStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'component_type', 'is_percentage', 'default_value', 'is_active']
    list_filter = ['component_type', 'is_taxable', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['staff', 'month', 'basic_salary', 'net_salary', 'status']
    list_filter = ['status', 'month']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff']


@admin.register(PayrollComponent)
class PayrollComponentAdmin(admin.ModelAdmin):
    list_display = ['payroll', 'structure_component', 'amount']
    list_filter = ['structure_component']
    search_fields = ['payroll__staff__user__first_name']
    raw_id_fields = ['payroll']


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['staff', 'review_period_start', 'review_period_end', 'review_date', 'overall_rating', 'reviewed_by']
    list_filter = ['review_date', 'overall_rating']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'reviewed_by']


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'trainer_name', 'venue']
    list_filter = ['start_date', 'end_date']
    search_fields = ['title', 'trainer_name']


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = ['training', 'staff', 'attended']
    list_filter = ['attended', 'training']
    search_fields = ['staff__user__first_name', 'training__title']
    raw_id_fields = ['staff']


@admin.register(StaffDisciplinaryAction)
class StaffDisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ['staff', 'action_type', 'severity', 'status', 'incident_date', 'reported_by']
    list_filter = ['status', 'action_type', 'severity', 'incident_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'reported_by', 'reviewed_by']


@admin.register(StaffSuspensionRequest)
class StaffSuspensionRequestAdmin(admin.ModelAdmin):
    list_display = ['staff', 'suspension_start_date', 'suspension_end_date', 'duration_days', 'status', 'requested_by']
    list_filter = ['status', 'suspension_start_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'requested_by', 'reviewed_by']


@admin.register(StaffTerminationRequest)
class StaffTerminationRequestAdmin(admin.ModelAdmin):
    list_display = ['staff', 'reason', 'effective_date', 'status', 'requested_by']
    list_filter = ['status', 'reason', 'effective_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'requested_by', 'reviewed_by']


# ============================================
# ALLOWANCES & DEDUCTIONS
# ============================================

@admin.register(StaffAllowance)
class StaffAllowanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'allowance_type', 'amount', 'frequency', 'status', 'start_date']
    list_filter = ['allowance_type', 'frequency', 'status', 'start_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'approved_by']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StaffDeduction)
class StaffDeductionAdmin(admin.ModelAdmin):
    list_display = ['staff', 'deduction_type', 'amount', 'frequency', 'status', 'start_date']
    list_filter = ['deduction_type', 'frequency', 'status', 'start_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['staff', 'approved_by']
    readonly_fields = ['created_at', 'updated_at']


# ============================================
# PAYSLIPS
# ============================================

@admin.register(PaySlip)
class PaySlipAdmin(admin.ModelAdmin):
    list_display = ['payslip_number', 'staff', 'payslip_period_start', 'payslip_period_end', 'gross_salary', 'net_salary', 'status']
    list_filter = ['status', 'payslip_period_start']
    search_fields = ['payslip_number', 'staff__user__first_name', 'staff__user__last_name']
    raw_id_fields = ['payroll', 'staff', 'generated_by', 'approved_by']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaySlipAllowance)
class PaySlipAllowanceAdmin(admin.ModelAdmin):
    list_display = ['payslip', 'description', 'amount']
    search_fields = ['payslip__payslip_number', 'description']
    raw_id_fields = ['payslip', 'allowance']


@admin.register(PaySlipDeduction)
class PaySlipDeductionAdmin(admin.ModelAdmin):
    list_display = ['payslip', 'description', 'amount']
    search_fields = ['payslip__payslip_number', 'description']
    raw_id_fields = ['payslip', 'deduction']


@admin.register(PayslipBatch)
class PayslipBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_number', 'batch_period_start', 'batch_period_end', 'payslips_generated', 'total_net', 'status']
    list_filter = ['status', 'batch_period_start']
    search_fields = ['batch_number']
    raw_id_fields = ['created_by', 'approved_by']
    readonly_fields = ['created_at']
