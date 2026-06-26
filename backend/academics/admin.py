from django.contrib import admin
from .models import (
    Subject, SubjectAllocation, Syllabus, Assignment, AssignmentSubmission,
    Exam, ExamResult, GradingScheme, ReportCard
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_elective', 'created_at']
    list_filter = ['is_elective']
    search_fields = ['name', 'code']


@admin.register(SubjectAllocation)
class SubjectAllocationAdmin(admin.ModelAdmin):
    list_display = ['subject', 'grade', 'teacher', 'academic_year', 'periods_per_week']
    list_filter = ['academic_year', 'grade']
    search_fields = ['subject__name', 'teacher__first_name', 'teacher__last_name']
    raw_id_fields = ['teacher']


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'grade', 'term', 'academic_year']
    list_filter = ['academic_year', 'term', 'grade', 'subject']
    search_fields = ['title', 'subject__name']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'classroom', 'teacher', 'assignment_type', 'due_date']
    list_filter = ['assignment_type', 'assigned_date', 'due_date', 'subject']
    search_fields = ['title', 'subject__name', 'teacher__first_name']
    raw_id_fields = ['teacher']


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submission_date', 'marks_obtained', 'is_late']
    list_filter = ['is_late', 'submission_date']
    search_fields = ['student__user__first_name', 'assignment__title']
    raw_id_fields = ['student']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'subject', 'classroom', 'term', 'exam_date']
    list_filter = ['exam_type', 'term', 'subject']
    search_fields = ['name']


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks_obtained', 'grade', 'is_absent']
    list_filter = ['exam', 'grade', 'is_absent']
    search_fields = ['student__user__first_name', 'student__admission_number']
    raw_id_fields = ['student']


@admin.register(GradingScheme)
class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_percentage', 'max_percentage', 'grade', 'grade_point']
    list_filter = ['grade']
    search_fields = ['name', 'grade']


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'overall_percentage', 'overall_grade', 'position_in_class']
    list_filter = ['term']
    search_fields = ['student__user__first_name', 'student__admission_number']
    raw_id_fields = ['student']
