from django.contrib import admin
from .models import PerformanceTrend, AttendanceTrend, EnrollmentPattern, TeacherWorkload, CustomReport
from .models_schedule import ReportSchedule, ReportLog


@admin.register(PerformanceTrend)
class PerformanceTrendAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'term', 'grade', 'classroom', 'average_percentage', 'pass_percentage']
    list_filter = ['academic_year', 'term', 'grade']
    search_fields = ['grade__name', 'classroom__name']


@admin.register(AttendanceTrend)
class AttendanceTrendAdmin(admin.ModelAdmin):
    list_display = ['month', 'grade', 'classroom', 'total_students', 'total_school_days', 'average_attendance_percentage']
    list_filter = ['month', 'grade']
    search_fields = ['grade__name', 'classroom__name']


@admin.register(EnrollmentPattern)
class EnrollmentPatternAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'month', 'total_students', 'new_admissions', 'withdrawals']
    list_filter = ['academic_year', 'month']
    search_fields = ['academic_year__name']


@admin.register(TeacherWorkload)
class TeacherWorkloadAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'academic_year', 'term', 'total_classes', 'total_periods_per_week', 'total_students']
    list_filter = ['academic_year', 'term']
    search_fields = ['teacher__first_name', 'teacher__last_name']
    raw_id_fields = ['teacher']


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'created_by', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['title', 'created_by__first_name']
    raw_id_fields = ['created_by']


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'next_run', 'last_run']
    list_filter = ['report_type', 'frequency', 'is_active']
    search_fields = ['name', 'recipients']
    readonly_fields = ['last_run', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'frequency', 'format', 'is_active')
        }),
        ('Email Settings', {
            'fields': ('recipients', 'email_subject', 'email_body')
        }),
        ('Filters', {
            'fields': ('filter_grade', 'filter_class', 'filter_date_from', 'filter_date_to'),
            'classes': ('collapse',)
        }),
        ('Schedule Information', {
            'fields': ('next_run', 'last_run', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_reports_now']
    
    def generate_reports_now(self, request, queryset):
        """Generate selected reports immediately"""
        from django.core.management import call_command
        
        for schedule in queryset:
            try:
                call_command('generate_reports', schedule_id=schedule.id, send_email=True)
                self.message_user(request, f'Successfully generated: {schedule.name}', level='SUCCESS')
            except Exception as e:
                self.message_user(request, f'Failed to generate {schedule.name}: {str(e)}', level='ERROR')
    
    generate_reports_now.short_description = 'Generate selected reports now'


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'status', 'file_size_display', 'email_sent', 'created_at', 'completed_at']
    list_filter = ['status', 'report_type', 'email_sent', 'created_at']
    search_fields = ['schedule__name', 'recipients', 'error_message']
    readonly_fields = ['created_at', 'completed_at', 'file_size_display']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('schedule', 'report_type', 'status', 'generated_by')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'file_size_display')
        }),
        ('Email Delivery', {
            'fields': ('recipients', 'email_sent', 'email_sent_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
