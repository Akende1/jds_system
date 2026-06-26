from django.contrib import admin
from .models import StudentAttendance, StaffAttendance, AttendanceSummary, DisciplineIncident, BehaviorLog


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'classroom', 'date', 'status', 'check_in_time', 'marked_by']
    list_filter = ['status', 'date', 'classroom']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    raw_id_fields = ['student', 'marked_by']
    date_hierarchy = 'date'


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'status', 'check_in_time', 'check_out_time', 'working_hours']
    list_filter = ['status', 'date']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'staff__employee_id']
    raw_id_fields = ['staff', 'marked_by']
    date_hierarchy = 'date'


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'month', 'total_school_days', 'days_present', 'days_absent', 'attendance_percentage']
    list_filter = ['month']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    raw_id_fields = ['student']


@admin.register(DisciplineIncident)
class DisciplineIncidentAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'incident_type', 'severity', 'reported_by', 'is_resolved']
    list_filter = ['severity', 'incident_type', 'is_resolved', 'date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'description']
    raw_id_fields = ['student', 'reported_by']
    date_hierarchy = 'date'


@admin.register(BehaviorLog)
class BehaviorLogAdmin(admin.ModelAdmin):
    list_display = ['student', 'behavior_type', 'title', 'points', 'recorded_by', 'date']
    list_filter = ['behavior_type', 'date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'title']
    raw_id_fields = ['student', 'recorded_by']
    date_hierarchy = 'date'
