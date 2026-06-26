from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    User, AcademicYear, Term, Grade, ClassRoom, 
    Student, Staff, SchoolInformation, StaffRole, Notification, ApprovalRequest
)
from .models_class_management import (
    ClassPromotion, StudentTransfer, TeacherAssignment, ClassStatistics,
    StudentSuspension, StudentExpulsion
)
from .models import EditRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'reports_to', 'is_active_user']
    list_filter = ['user_type', 'is_active_user', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'date_of_birth', 
                      'address', 'emergency_contact', 'is_active_user')
        }),
        ('Hierarchy', {
            'fields': ('reports_to',),
            'description': 'Set the direct supervisor/manager for this user in the organizational hierarchy'
        }),
    )


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    search_fields = ['name']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'term_number', 'start_date', 'end_date', 'is_current']
    list_filter = ['academic_year', 'term_number', 'is_current']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'level']
    ordering = ['level']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'class_teacher', 'room_number', 'capacity', 'student_count']
    list_filter = ['grade', 'section', 'academic_year']
    search_fields = ['grade__name', 'section', 'room_number']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'current_class', 'gender', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'current_class__grade', 'gender']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name', 'guardian_name']
    date_hierarchy = 'admission_date'


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'user', 'staff_type', 'employment_type', 'designation', 'is_active']
    list_filter = ['staff_type', 'employment_type', 'is_active']
    search_fields = ['staff_id', 'user__first_name', 'user__last_name', 'designation']
    date_hierarchy = 'date_of_joining'
    readonly_fields = ['digital_signature_preview']

    fieldsets = (
        ('Staff Profile', {
            'fields': ('user', 'staff_id', 'staff_type', 'employment_type', 'is_active')
        }),
        ('Employment Details', {
            'fields': ('date_of_joining', 'department', 'designation', 'qualification', 'experience_years', 'gender', 'marital_status')
        }),
        ('Banking Details', {
            'fields': ('bank_name', 'account_number')
        }),
        ('Onboarding Documents', {
            'fields': ('tpin_no', 'nrc_no', 'nrc_front', 'nrc_back', 'other_documents')
        }),
        ('Digital Signature', {
            'fields': ('digital_signature', 'digital_signature_preview')
        }),
    )

    def digital_signature_preview(self, obj):
        if obj and obj.digital_signature:
            return format_html('<img src="{}" style="max-height: 72px; max-width: 220px; object-fit: contain; border: 1px solid #e5e7eb; padding: 4px; border-radius: 8px; background: #fff;" />', obj.digital_signature.url)
        return 'No signature uploaded yet.'

    digital_signature_preview.short_description = 'Signature Preview'


@admin.register(SchoolInformation)
class SchoolInformationAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'school_code', 'email', 'phone']
    readonly_fields = ['logo_preview', 'principal_signature_preview']

    fieldsets = (
        ('Branding', {
            'fields': ('school_name', 'school_code', 'motto', 'logo', 'logo_preview')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'website', 'address', 'city', 'state', 'country')
        }),
        ('Principal Details', {
            'fields': ('principal_name', 'principal_signature', 'principal_signature_preview')
        }),
    )
    
    def logo_preview(self, obj):
        if obj and obj.logo:
            return format_html('<img src="{}" style="max-height: 88px; max-width: 240px; object-fit: contain; border: 1px solid #e5e7eb; padding: 4px; border-radius: 8px; background: #fff;" />', obj.logo.url)
        return 'No logo uploaded yet.'

    logo_preview.short_description = 'Logo Preview'

    def principal_signature_preview(self, obj):
        if obj and obj.principal_signature:
            return format_html('<img src="{}" style="max-height: 72px; max-width: 220px; object-fit: contain; border: 1px solid #e5e7eb; padding: 4px; border-radius: 8px; background: #fff;" />', obj.principal_signature.url)
        return 'No signature uploaded yet.'

    principal_signature_preview.short_description = 'Principal Signature Preview'
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SchoolInformation.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


# ============ Class Management Models ============

@admin.register(ClassPromotion)
class ClassPromotionAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_class', 'to_class', 'status', 'final_percentage', 'promotion_date']
    list_filter = ['status', 'academic_year', 'promotion_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    date_hierarchy = 'promotion_date'
    readonly_fields = ['approved_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Student & Classes', {
            'fields': ('student', 'from_class', 'to_class', 'academic_year')
        }),
        ('Performance Metrics', {
            'fields': ('final_percentage', 'attendance_percentage')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('promotion_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_promotions', 'reject_promotions']
    
    def approve_promotions(self, request, queryset):
        """Approve selected promotions"""
        for promotion in queryset.filter(status='pending'):
            try:
                promotion.approve(request.user)
                self.message_user(request, f'Approved promotion for {promotion.student}', level='SUCCESS')
            except Exception as e:
                self.message_user(request, f'Failed to approve {promotion.student}: {str(e)}', level='ERROR')
    
    approve_promotions.short_description = 'Approve selected promotions'
    
    def reject_promotions(self, request, queryset):
        """Reject selected promotions"""
        for promotion in queryset.filter(status='pending'):
            try:
                promotion.reject(request.user, reason='Rejected by admin')
                self.message_user(request, f'Rejected promotion for {promotion.student}', level='WARNING')
            except Exception as e:
                self.message_user(request, f'Failed to reject {promotion.student}: {str(e)}', level='ERROR')
    
    reject_promotions.short_description = 'Reject selected promotions'


@admin.register(StudentTransfer)
class StudentTransferAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_class', 'to_class', 'transfer_type', 'status', 'requested_date']
    list_filter = ['transfer_type', 'status', 'requested_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    date_hierarchy = 'requested_date'
    readonly_fields = ['requested_date', 'approved_date', 'transfer_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transfer Details', {
            'fields': ('student', 'from_class', 'to_class', 'transfer_type', 'reason')
        }),
        ('Workflow', {
            'fields': ('status', 'requested_by', 'requested_date', 'approved_by', 'approved_date', 'transfer_date')
        }),
        ('Additional Information', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_and_execute_transfers']
    
    def approve_and_execute_transfers(self, request, queryset):
        """Approve and execute selected transfers"""
        for transfer in queryset.filter(status='requested'):
            try:
                transfer.approve_and_execute(request.user)
                self.message_user(request, f'Executed transfer for {transfer.student}', level='SUCCESS')
            except Exception as e:
                self.message_user(request, f'Failed to transfer {transfer.student}: {str(e)}', level='ERROR')
    
    approve_and_execute_transfers.short_description = 'Approve & execute selected transfers'


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject_name', 'classroom', 'periods_per_week', 'is_active', 'academic_year']
    list_filter = ['is_active', 'academic_year', 'term', 'classroom__grade']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'subject_name']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('teacher', 'classroom', 'subject_name', 'periods_per_week')
        }),
        ('Academic Period', {
            'fields': ('academic_year', 'term', 'is_active')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Additional Notes', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassStatistics)
class ClassStatisticsAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'total_students', 'gender_ratio', 'average_attendance_rate', 
                   'fee_collection_rate', 'last_calculated']
    list_filter = ['academic_year', 'term', 'classroom__grade']
    search_fields = ['classroom__grade__name']
    readonly_fields = ['last_calculated']
    
    fieldsets = (
        ('Class Information', {
            'fields': ('classroom', 'academic_year', 'term')
        }),
        ('Student Demographics', {
            'fields': ('total_students', 'male_students', 'female_students')
        }),
        ('Academic Performance', {
            'fields': ('average_percentage', 'top_performer_percentage', 'lowest_percentage')
        }),
        ('Attendance', {
            'fields': ('average_attendance_rate',)
        }),
        ('Financial', {
            'fields': ('total_fees_expected', 'total_fees_collected', 'fee_collection_rate')
        }),
        ('Last Update', {
            'fields': ('last_calculated',)
        }),
    )
    
    actions = ['recalculate_statistics']
    
    def gender_ratio(self, obj):
        if obj.total_students > 0:
            male_pct = (obj.male_students / obj.total_students) * 100
            female_pct = (obj.female_students / obj.total_students) * 100
            return f"M: {male_pct:.0f}% / F: {female_pct:.0f}%"
        return "N/A"
    gender_ratio.short_description = 'Gender Ratio'
    
    def recalculate_statistics(self, request, queryset):
        """Recalculate statistics for selected classes"""
        for stat in queryset:
            try:
                ClassStatistics.calculate_for_class(stat.classroom, stat.academic_year, stat.term)
                self.message_user(request, f'Recalculated stats for {stat.classroom}', level='SUCCESS')
            except Exception as e:
                self.message_user(request, f'Failed to recalculate {stat.classroom}: {str(e)}', level='ERROR')
    
    recalculate_statistics.short_description = 'Recalculate selected statistics'


@admin.register(StudentSuspension)
class StudentSuspensionAdmin(admin.ModelAdmin):
    list_display = ['student', 'suspension_start_date', 'suspension_end_date', 'status', 'requested_by']
    list_filter = ['status', 'suspension_start_date', 'reason']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    raw_id_fields = ['student', 'requested_by', 'approved_by']


@admin.register(EditRequest)
class EditRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'field_name', 'parent', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__admission_number', 'student__user__first_name', 'parent__username', 'field_name']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at', 'reviewed_by']
    fieldsets = (
        ('Request', {'fields': ('parent', 'student', 'field_name', 'requested_value')}),
        ('Workflow', {'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    actions = ['approve_requests', 'reject_requests']

    SAFE_FIELD_MAP = {
        'guardian_phone': 'guardian_phone',
        'guardian_email': 'guardian_email',
        'guardian_name': 'guardian_name',
        'guardian_address': 'guardian_address',
    }

    def approve_requests(self, request, queryset):
        """Approve selected requests and apply safe edits to Student records."""
        import datetime
        applied = 0
        for req in queryset.filter(status='pending'):
            field = req.field_name
            if field in self.SAFE_FIELD_MAP:
                student = req.student
                setattr(student, self.SAFE_FIELD_MAP[field], req.requested_value)
                student.save()
                req.status = 'approved'
                req.reviewed_by = request.user
                req.reviewed_at = datetime.datetime.now()
                req.save()
                applied += 1
            else:
                # mark as rejected if field not allowed
                req.status = 'rejected'
                req.reviewed_by = request.user
                req.reviewed_at = datetime.datetime.now()
                req.admin_notes = 'Field not allowed for automatic approval.'
                req.save()

        self.message_user(request, f'Approved and applied edits for {applied} requests.')

    approve_requests.short_description = 'Approve & apply selected edit requests'

    def reject_requests(self, request, queryset):
        import datetime
        for req in queryset.filter(status='pending'):
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = datetime.datetime.now()
            req.save()
        self.message_user(request, f'Rejected {queryset.filter(status="rejected").count()} requests.')

    reject_requests.short_description = 'Reject selected edit requests'


@admin.register(StudentExpulsion)
class StudentExpulsionAdmin(admin.ModelAdmin):
    list_display = ['student', 'reason', 'recommendation_date', 'status', 'recommended_by']
    list_filter = ['status', 'reason', 'recommendation_date']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    raw_id_fields = ['student', 'recommended_by', 'reviewed_by', 'approved_by']


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ['staff', 'role_type', 'assigned_date', 'is_active']
    list_filter = ['role_type', 'is_active', 'assigned_date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'staff__staff_id']
    date_hierarchy = 'assigned_date'
    readonly_fields = ['assigned_date', 'created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'status', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['title', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Info', {
            'fields': ('recipient', 'notification_type', 'title', 'message', 'status')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['request_type', 'status', 'requested_by', 'reviewed_by', 'created_at']
    list_filter = ['request_type', 'status', 'created_at']
    search_fields = ['requested_by__username', 'requested_by__first_name', 'requested_by__last_name', 'remarks']
    readonly_fields = ['created_at', 'reviewed_at']
    filter_horizontal = ['assigned_to']
