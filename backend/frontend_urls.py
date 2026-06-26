"""
Frontend URL patterns for daily operations
These replace Django Admin for most user-facing tasks
"""
from django.urls import path
from administration import dashboard_views, student_views, finance_views, staff_views, payroll_views
from attendance import views as attendance_views
from academics import views as academics_views
from analytics import views as analytics_views
from sync import views as sync_views
from communication import views as communication_views
from portals import views as portals_views

teacher_communication_hub = getattr(communication_views, 'teacher_communication_hub')
# Other view imports will be added as modules are implemented

app_name = 'frontend'

urlpatterns = [
    # ============================================
    # DASHBOARD ROUTES
    # ============================================
    path('', dashboard_views.dashboard_router, name='dashboard'),
    
    # ============================================
    # ADMINISTRATION ROUTES
    # ============================================
    
    # Students
    path('students/', student_views.student_list, name='student_list'),
    path('students/export/', student_views.student_export, name='student_export'),
    path('students/register/', student_views.student_register, name='student_register'),
    path('students/<int:pk>/', student_views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', student_views.student_edit, name='student_edit'),
    path('students/promote/', student_views.student_promote, name='student_promote'),
    path('students/transfer/', student_views.student_transfer, name='student_transfer'),
    
    # Student Discipline
    path('students/suspensions/', student_views.student_suspension_list, name='student_suspension_list'),
    path('students/<int:pk>/suspend/', student_views.student_suspension_request, name='student_suspend'),
    path('students/suspension/<int:pk>/', student_views.student_suspension_detail, name='student_suspension_detail'),
    path('students/expulsions/', student_views.student_expulsion_list, name='student_expulsion_list'),
    path('students/<int:pk>/expel/', student_views.student_expulsion_recommend, name='student_expulsion_recommend'),
    path('students/expulsion/<int:pk>/', student_views.student_expulsion_detail, name='student_expulsion_detail'),
    
    # Staff (to be implemented)
    # path('staff/', staff_views.staff_list, name='staff_list'),
    # path('staff/<int:pk>/', staff_views.staff_detail, name='staff_detail'),
    # path('staff/add/', staff_views.staff_add, name='staff_add'),
    # path('staff/<int:pk>/assign/', staff_views.staff_assign_classes, name='staff_assign'),
    
    # Classes (to be implemented)
    # path('classes/', views.class_list, name='class_list'),
    # path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    # path('classes/<int:pk>/students/', views.class_students, name='class_students'),
    # path('classes/<int:pk>/timetable/', views.class_timetable, name='class_timetable'),
    
    # ============================================
    # FINANCE ROUTES
    # ============================================
    
    # Invoices
    path('finance/invoices/', finance_views.invoice_list, name='invoice_list'),
    path('finance/invoices/generate/', finance_views.invoice_generate, name='invoice_generate'),
    path('finance/invoices/<int:pk>/', finance_views.invoice_detail, name='invoice_detail'),
    path('finance/fee-structures/', finance_views.fee_structure_list, name='fee_structure_list'),
    path('finance/fee-structures/add/', finance_views.fee_structure_add, name='fee_structure_add'),
    
    # Payments
    path('finance/payments/', finance_views.payment_list, name='payment_list'),
    path('finance/payments/record/', finance_views.payment_record, name='payment_record'),
    path('finance/payments/<int:pk>/', finance_views.payment_detail, name='payment_detail'),
    path('finance/payments/<int:pk>/receipt/', finance_views.payment_receipt, name='payment_receipt'),
    
    # Accounts
    path('finance/accounts/', finance_views.accounts_list, name='accounts_list'),
    path('finance/accounts/<int:student_id>/', finance_views.student_account, name='student_account'),
    path('finance/arrears/', finance_views.arrears_list, name='arrears_list'),
    path('finance/reminders/', finance_views.send_reminders, name='send_reminders'),
    
    # Expenses
    path('finance/expenses/', finance_views.expense_list, name='expense_list'),
    path('finance/expenses/add/', finance_views.expense_add, name='expense_add'),

    # Inventory
    path('finance/inventory/', dashboard_views.manager_inventory_dashboard, name='inventory_dashboard'),
    
    # ============================================
    # STAFF ROUTES
    # ============================================
    path('staff/', staff_views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', staff_views.staff_detail, name='staff_detail'),
    path('staff/add/', staff_views.staff_add, name='staff_add'),
    path('staff/<int:pk>/complete/', staff_views.staff_complete_profile, name='staff_complete_profile'),
    path('staff/onboarding/<str:token>/', staff_views.staff_onboarding_complete, name='staff_onboarding_complete'),
    path('staff/<int:pk>/assign/', staff_views.staff_assign_classes, name='staff_assign'),
    path('staff/<int:pk>/promote/', staff_views.staff_promote_to_head, name='staff_promote'),
    
    # Staff Discipline
    path('staff/disciplinary/', staff_views.staff_disciplinary_action_list, name='staff_disciplinary_list'),
    path('staff/<int:pk>/disciplinary/report/', staff_views.staff_disciplinary_action_report, name='staff_disciplinary_report'),
    path('staff/disciplinary/<int:pk>/', staff_views.staff_disciplinary_action_detail, name='staff_disciplinary_detail'),
    path('staff/suspensions/', staff_views.staff_suspension_request_list, name='staff_suspension_list'),
    path('staff/<int:pk>/suspend/', staff_views.staff_suspension_request_create, name='staff_suspension_create'),
    path('staff/suspension/<int:pk>/', staff_views.staff_suspension_request_detail, name='staff_suspension_detail'),
    path('staff/terminations/', staff_views.staff_termination_request_list, name='staff_termination_list'),
    path('staff/<int:pk>/terminate/', staff_views.staff_termination_request_create, name='staff_termination_create'),
    path('staff/termination/<int:pk>/', staff_views.staff_termination_request_detail, name='staff_termination_detail'),
    
    # ============================================
    # ATTENDANCE ROUTES
    # ============================================
    path('attendance/', attendance_views.student_attendance_list, name='attendance_list'),
    path('attendance/mark/', attendance_views.mark_attendance, name='attendance_mark'),
    path('attendance/summary/', attendance_views.attendance_summary, name='attendance_summary'),
    path('attendance/staff/', attendance_views.staff_attendance_list, name='staff_attendance_list'),
    
    # ============================================
    # ACADEMICS ROUTES
    # ============================================
    path('academics/', academics_views.subject_list, name='academics_home'),
    path('academics/subjects/', academics_views.subject_list, name='subject_list'),
    path('academics/exams/', academics_views.exam_list, name='exam_list'),
    path('academics/exams/new/', academics_views.exam_create, name='exam_create'),
    path('academics/exams/<int:pk>/scores/', academics_views.exam_score_entry, name='exam_score_entry'),
    path('academics/timetable/', academics_views.timetable_view, name='timetable'),
    path('academics/timetable/', academics_views.timetable_view, name='timetable_view'),
    path('academics/timetable/new/', academics_views.timetable_create, name='timetable_create'),
    path('academics/timetable/<int:pk>/edit/', academics_views.timetable_edit, name='timetable_edit'),
    path('api/academics/timetable/check-conflicts/', academics_views.check_timetable_conflicts, name='check_timetable_conflicts'),
    path('academics/calendar/', academics_views.academic_calendar_view, name='calendar'),
    path('academics/calendar/', academics_views.academic_calendar_view, name='academic_calendar_view'),
    path('academics/calendar/new/', academics_views.academic_calendar_create, name='calendar_create'),
    path('academics/results/', academics_views.result_list, name='result_list'),
    path('academics/results/<int:pk>/', academics_views.result_detail, name='result_detail'),
    path('academics/report-cards/<int:student_id>/', academics_views.report_card_view, name='report_card_view'),
    path('academics/report-cards/edit/<int:pk>/', academics_views.report_card_edit, name='report_card_edit'),
    
    # ============================================
    # ANALYTICS ROUTES
    # ============================================
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/performance/', analytics_views.student_performance_analytics, name='analytics_performance'),
    path('analytics/financial/', analytics_views.financial_analytics, name='analytics_financial'),

    # ============================================
    # SYNC ROUTES
    # ============================================
    path('sync/', sync_views.sync_dashboard, name='sync_dashboard'),

    # ============================================
    # PORTAL / NOTIFICATION ROUTES
    # ============================================
    path('notifications/', portals_views.notifications_view, name='notifications'),

    # Parent edit request (submit a requested change to student record)
    path('parent/request-edit/', dashboard_views.submit_edit_request, name='submit_edit_request'),

    # ============================================
    # TEACHER COMMUNICATION ROUTES
    # ============================================
    path('communication/teacher/', teacher_communication_hub, name='teacher_communication_hub'),
    
    # ============================================
    # FINANCIAL MANAGEMENT ROUTES
    # ============================================
    path('financial/', payroll_views.financial_overview, name='financial_overview'),
    path('financial/income/', payroll_views.income_list, name='income_list'),
    path('financial/expenses/', payroll_views.expense_list, name='expense_list'),
    path('financial/expenses/add/', payroll_views.expense_add, name='expense_add'),
    path('financial/salaries/', payroll_views.salary_list, name='salary_list'),
    path('financial/salaries/<int:pk>/', payroll_views.salary_detail, name='salary_detail'),
    path('financial/reports/', payroll_views.financial_reports, name='financial_reports'),
    
    # ============================================
    # PAYROLL MANAGEMENT ROUTES
    # ============================================
    
    # Allowances
    path('payroll/allowances/', payroll_views.allowance_list, name='payroll_allowance_list'),
    path('payroll/allowances/staff/<int:staff_id>/add/', payroll_views.allowance_create, name='payroll_allowance_create'),
    path('payroll/allowances/<int:pk>/', payroll_views.allowance_detail, name='payroll_allowance_detail'),
    path('payroll/allowances/<int:pk>/edit/', payroll_views.allowance_edit, name='payroll_allowance_edit'),
    path('payroll/allowances/<int:pk>/end/', payroll_views.allowance_end, name='payroll_allowance_end'),
    
    # Deductions
    path('payroll/deductions/', payroll_views.deduction_list, name='payroll_deduction_list'),
    path('payroll/deductions/staff/<int:staff_id>/add/', payroll_views.deduction_create, name='payroll_deduction_create'),
    path('payroll/deductions/<int:pk>/', payroll_views.deduction_detail, name='payroll_deduction_detail'),
    path('payroll/deductions/<int:pk>/edit/', payroll_views.deduction_edit, name='payroll_deduction_edit'),
    path('payroll/deductions/<int:pk>/end/', payroll_views.deduction_end, name='payroll_deduction_end'),
    
    # Payslips
    path('payroll/payslips/', payroll_views.payslip_list, name='payroll_payslip_list'),
    path('payroll/payslips/<int:pk>/', payroll_views.payslip_detail, name='payroll_payslip_detail'),
    path('payroll/payslips/<int:pk>/approve/', payroll_views.payslip_approve, name='payroll_payslip_approve'),
    path('payroll/payslips/<int:pk>/issue/', payroll_views.payslip_issue, name='payroll_payslip_issue'),
    path('payroll/staff/<int:staff_id>/payslip-history/', payroll_views.staff_payslip_history, name='payroll_staff_payslip_history'),
    
    # Payslip Batches
    path('payroll/batches/', payroll_views.payslip_batch_list, name='payroll_payslip_batch_list'),
    path('payroll/batches/<int:pk>/', payroll_views.payslip_batch_detail, name='payroll_payslip_batch_detail'),
    path('payroll/batches/<int:pk>/approve/', payroll_views.payslip_batch_approve, name='payroll_payslip_batch_approve'),
    
    # ============================================
    # STOCK MANAGEMENT & RESTOCKING ROUTES
    # ============================================
    path('cooking/dashboard/', dashboard_views.cooking_staff_dashboard, name='cooking_staff_dashboard'),
    path('cooking/restocking/', dashboard_views.submit_restocking_request, name='restocking_form'),
    path('teacher/stationery-request/', dashboard_views.submit_restocking_request, name='stationery_request'),
    path('manager/approvals/', dashboard_views.manager_approvals_dashboard, name='manager_approvals'),
    path('manager/restocking/<int:request_id>/approve/', dashboard_views.approve_restocking_request, name='approve_restocking'),
    path('manager/restocking/<int:request_id>/reject/', dashboard_views.reject_restocking_request, name='reject_restocking'),
    path('manager/approval/<int:approval_id>/approve/', dashboard_views.approve_approval_request, name='approve_approval'),
    path('manager/approval/<int:approval_id>/reject/', dashboard_views.reject_approval_request, name='reject_approval'),
    
    # ============================================
    # ADDITIONAL ROUTES (TO BE IMPLEMENTED IN PHASE 2)
    # ============================================
    # Uncomment and implement views as needed:
    
    # COMMUNICATION ROUTES
    # path('announcements/', views.announcement_list, name='announcement_list'),
    # path('messages/', views.message_list, name='message_list'),
    
    # TRANSPORT ROUTES
    # path('transport/routes/', views.route_list, name='route_list'),
    
    # LUNCH ROUTES
    # path('lunch/daily/', views.lunch_daily_list, name='lunch_daily'),
    
    # HR ROUTES
    # path('hr/leave/', views.leave_list, name='leave_list'),
    
    # LMS ROUTES
    # path('lms/courses/', views.course_list, name='course_list'),
    
    # ANALYTICS ROUTES
    # path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # SYNC ROUTES
    # path('sync/', views.sync_dashboard, name='sync_dashboard'),
]
