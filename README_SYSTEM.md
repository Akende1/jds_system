# JDS School Management System - Comprehensive System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Module Descriptions](#module-descriptions)
4. [User Roles & Permissions](#user-roles--permissions)
5. [Feature Matrix](#feature-matrix)
6. [Workflows & Processes](#workflows--processes)
7. [Database Models](#database-models)
8. [API & URLs](#api--urls)
9. [Setup & Deployment](#setup--deployment)

---

## System Overview

**JDS School Management System** is an enterprise-grade Django-based virtual marketplace for comprehensive school management. It provides integrated solutions for academics, HR, finance, attendance, communication, and discipline management.

### Key Capabilities
- 📚 Academic Management (Classes, Exams, Timetables, Report Cards)
- 👥 Staff & Student Management with Discipline Workflows
- 💰 Comprehensive Finance & Payroll System with Accounting
- ⏰ Attendance Tracking (Students & Staff)
- 📢 Communication & Notifications
- 📊 Analytics & Reporting
- 🔐 Role-Based Access Control (RBAC)
- 🔄 Approval Workflows for Critical Operations

### Technology Stack
- **Framework**: Django 4.x (Python)
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Frontend**: HTML/CSS/JavaScript with Django Templates
- **Authentication**: Custom Django User model with role-based decorators

---

## Architecture

### Multi-App Structure
```
backend/
├── academics/         # Courses, Exams, Timetables, Results
├── administration/    # Staff, Students, Discipline, Classes
├── analytics/         # Data Analysis & Reporting
├── attendance/        # Student & Staff Attendance
├── communication/     # Messaging, Announcements, Emails
├── finance/           # Invoicing, Payments, Budgeting, Accounting
├── hr/                # Payroll, Leave, Performance, Allowances
├── inventory/         # Asset & Equipment Management
├── lms/               # Learning Management Features
├── portals/           # Parent, Student, Teacher Portals
├── school_management/ # Main Project Settings
├── security/          # Security & Compliance
├── sync/              # Data Synchronization
└── transport/         # Transportation Management
```

### Database Design
- **Modular**: Each app manages its own models
- **Relationships**: Foreign keys & many-to-many for cross-app queries
- **Status Tracking**: State machines for workflows (draft → approved → active → completed)
- **Audit Trail**: Timestamps (`created_at`, `updated_at`) on all models
- **User Hierarchy**: `reports_to` field enables organizational structure

### Permission Model
```
Django User Model (Extended)
├── user_type (admin, manager, head_teacher, teacher, auxiliary, parent, student)
├── is_active (boolean)
├── onboarding_completed (boolean)
└── staff_id (unique identifier for staff)
```

---

## Module Descriptions

### 1. **Administration Module** (`backend/administration/`)
Manages staff, students, classes, and organizational structure.

#### Key Models
- **Staff**: Employee records with salary, department, contacts
- **Student**: Enrollment, grade, class assignments
- **ClassRoom**: Class structure with teachers and students
- **TeacherAssignment**: Subject assignments per grade
- **StaffDisciplinaryAction**: Track staff infractions and actions
- **StaffSuspensionRequest**: Formal suspension workflow with pay control
- **StaffTerminationRequest**: Dismissal process with severance tracking
- **StudentSuspension**: Student suspension workflow with appeal capability
- **StudentExpulsion**: Multi-level expulsion approval process

#### Key Views
- `staff_list()` - All staff members
- `staff_detail()` - Individual profile with payslips & allowances
- `staff_promote_to_head()` - Promote teacher to head teacher
- `staff_disciplinary_action_list/detail()` - Manage staff discipline
- `student_list()`, `student_detail()`
- `student_suspension_list/request/detail()` - Student suspension workflow
- `student_expulsion_list/recommend/detail()` - Expulsion approval chain

#### Permissions
- **Manager/Admin**: Full access to all staff/student operations
- **Head Teacher**: View own staff/students in their schools
- **Teacher**: View student records, mark attendance

---

### 2. **HR Module** (`backend/hr/`)
Comprehensive human resources including payroll, leave, performance, and compensation.

#### Key Models
- **LeaveType**: Paid/unpaid leave types with quotas
- **LeaveApplication**: Leave requests with approval workflow
- **PayrollStructure**: Define salary components (earnings, deductions)
- **Payroll**: Monthly payroll summary per staff member
- **PayrollComponent**: Individual line items in payroll
- **StaffAllowance**: Recurring allowances (housing, transport, medical, performance)
- **StaffDeduction**: Recurring deductions (tax, pension, insurance, loans)
- **PaySlip**: Formal payslip document with earnings/deductions breakdown
- **PaySlipAllowance**: Specific allowances on a payslip
- **PaySlipDeduction**: Specific deductions on a payslip
- **PayslipBatch**: Batch processing of multiple payslips
- **PerformanceReview**: Annual performance evaluations
- **Training**: Training programs and attendance tracking
- **Contract**: Employment contracts with terms

#### Key Workflows
1. **Leave Management**
   - Staff applies for leave
   - Manager/Head Teacher approves
   - System marks absent days on attendance

2. **Payroll Processing**
   - Configure allowances/deductions per employee
   - System calculates monthly payroll
   - Generate payslips with breakdown
   - Manager approves, then issues to employee

3. **Allowances**
   - Housing, transport, medical, meal, performance bonuses
   - Can be fixed amount or percentage-based
   - Active/Suspended/Ended status
   - Automatically included in payslip calculations

4. **Deductions**
   - Income tax, pension, health insurance, loan repayment
   - Fixed or percentage-based
   - Approval workflow required
   - Tracked with start/end dates

#### Key Views
- `allowance_list/create/detail/edit/end()` - Manage allowances
- `deduction_list/create/detail/edit/end()` - Manage deductions
- `payslip_list/detail/approve/issue()` - Payslip management
- `staff_payslip_history()` - View employee payslip history with trends
- `payslip_batch_list/detail/approve()` - Batch payslip processing

#### Permissions
- **Manager/Admin**: Full payroll control, approve allowances/deductions
- **Staff**: View own payslips (read-only)

---

### 3. **Finance Module** (`backend/finance/`)
Complete financial management including invoicing, payments, accounting, budgeting, and reconciliation.

#### Key Models - Core Finance
- **FeeStructure**: Define fee types (tuition, registration, meals)
- **FeeInvoice**: Student invoices with payment tracking
- **Payment**: Record student payments with methods (cash, bank, mobile money)
- **PaymentReceipt**: Formal receipts for audit trail

#### Key Models - Accounting Foundation
- **BankAccount**: Track all school bank accounts
- **ChartOfAccounts**: General ledger chart defining asset/liability/equity/income/expense accounts
- **GeneralLedgerEntry**: Individual debit/credit transactions for audit trail
- **Expense**: Expense records linked to chart of accounts

#### Key Models - Approval Workflows
- **ExpenseApprovalLevel**: Define approval tiers by role and amount threshold
- **ExpenseApprovalWorkflow**: Track multi-tier approval state for expenses
- **ExpenseApproval**: Individual approval decision records

#### Key Models - Budgeting & Reconciliation
- **BudgetAllocation**: Budget per expense category per academic year
- **BankReconciliation**: Monthly bank-to-system variance tracking
- **BankStatement**: Bank statement imports with transaction matching
- **BankTransaction**: Individual bank transactions (debit/credit)

#### Key Workflows
1. **Student Fee Management**
   - Admin creates fee invoice from student fee structure
   - Student pays via any supported method
   - System records payment and generates receipt
   - Automatic receipt numbering and audit trail

2. **Expense Management with Approvals**
   - Staff submits expense with supporting documents
   - Routed through approval chain:
     - **Level 1**: Head Teacher (expenses up to 10,000)
     - **Level 2**: Manager (expenses 10,000 - 50,000)
     - **Level 3**: Admin (expenses > 50,000)
   - Approved expenses linked to chart of accounts
   - Posted to general ledger

3. **Budgeting**
   - Admin allocates budget per category per academic year
   - System tracks spent vs. remaining in real-time
   - Alerts when approaching budget limit
   - Year-end variance analysis

4. **Bank Reconciliation**
   - Import bank statements monthly
   - Match transactions to system records
   - Identify discrepancies automatically
   - Reconciliation sign-off by finance manager

#### Key Views
- `financial_overview()` - Dashboard with income/expense summary
- `invoice_list/detail/generate()` - Fee invoicing
- `payment_list/record/detail()` - Payment recording
- `expense_list/add()` - Expense tracking with approval routing
- `financial_reports()` - Income/Expense/Payroll reports by date range

#### Permissions
- **Admin**: Full finance control
- **Manager**: Approve expenses up to threshold, view reports
- **Head Teacher**: Submit expenses, approve Level 1
- **Staff**: Submit expenses for approval

---

### 4. **Academics Module** (`backend/academics/`)
Academic planning, exams, grading, and reporting.

#### Key Models
- **Subject**: Course subjects with codes
- **Grade**: Grade levels (Primary 1, Secondary 4)
- **Exam**: Exam definitions with pass marks
- **ExamScore**: Student scores per exam
- **TimeTable**: Class schedules with room assignments
- **ReportCard**: Student academic performance reports

#### Key Views
- `subject_list()` - All subjects
- `exam_list/create()` - Exam management
- `exam_score_entry()` - Record exam results
- `timetable_view/create/edit()` - Schedule management
- `report_card_view/edit()` - Student report generation

#### Permissions
- **Teacher**: Record exam scores, view class timetable
- **Head Teacher**: Create exams, generate report cards
- **Admin**: Full academic control

---

### 5. **Attendance Module** (`backend/attendance/`)
Track attendance for students and staff with reporting.

#### Key Models
- **StudentAttendance**: Daily student attendance records
- **StaffAttendance**: Daily staff attendance records

#### Key Views
- `student_attendance_list()` - Mark student attendance
- `staff_attendance_list()` - Mark staff attendance
- `attendance_summary()` - Attendance reports

#### Permissions
- **Teacher**: Mark class attendance
- **Manager**: View attendance reports
- **Admin**: Full attendance control

---

### 6. **Communication Module** (`backend/communication/`)
Internal messaging, announcements, and email notifications.

#### Key Models
- **Message**: Staff-to-staff or admin-to-staff messages
- **Announcement**: School-wide announcements
- **EmailTemplate**: Reusable email templates
- **StudentContact**, **ParentContact**: Contact management

#### Key Views
- `teacher_communication_hub()` - Teacher messaging interface
- `announcement_list/create()` - Announcements

#### Permissions
- **Admin**: Send announcements to all
- **Manager/Head Teacher**: Send messages to staff
- **Teacher**: Send messages to other teachers

---

### 7. **Analytics Module** (`backend/analytics/`)
Data analysis, dashboards, and insights.

#### Key Models
- Custom views/aggregations (no direct models)

#### Key Views
- `analytics_dashboard()` - Main analytics home
- `student_performance_analytics()` - Academic performance trends
- `financial_analytics()` - Financial metrics & trends

#### Permissions
- **Manager/Admin**: Full access
- **Head Teacher**: Limited to own school data

---

### 8. **Additional Modules** (Brief Overview)
- **Security**: User permissions, role definitions, audit logs
- **Portals**: Parent portal, student portal, teacher portal
- **Inventory**: Asset management and equipment tracking
- **Transport**: Transportation routes and management
- **LMS**: Learning management and online content
- **Sync**: Data synchronization with external systems

---

## User Roles & Permissions

### 1. **Admin** (Super User)
Full system access. All operations unrestricted.
- Can access all menus
- Can manage users, roles, settings
- Can approve all workflows
- Can override any setting

**Dashboard**: Executive dashboard with all metrics
**Key Operations**: System configuration, user management, financial oversight

---

### 2. **Manager** (School Administrator)
Manages school operations, staff, finance, and approvals.

**Dashboard**: Operations dashboard with staff, finance, and attendance
**Capabilities**:
- ✅ Manage staff (hire, promote, discipline, suspend, terminate)
- ✅ Manage students (enroll, promote, suspend, expel)
- ✅ Manage classes and assignments
- ✅ Approve expenses up to threshold
- ✅ Process payroll and allowances/deductions
- ✅ View financial reports
- ✅ Manage academic calendar and exams
- ✅ Generate payslips
- ✅ View analytics

**Restricted**:
- ❌ Cannot delete users (archive only)
- ❌ Cannot change system settings
- ❌ Cannot exceed budget allocations

---

### 3. **Head Teacher** (School Administrator)
Manages academic operations and staff for their school.

**Dashboard**: Academic dashboard with classes, exams, attendance
**Capabilities**:
- ✅ Manage classes and teacher assignments
- ✅ Create and grade exams
- ✅ Generate report cards
- ✅ Approve Level 1 expenses
- ✅ View own staff payslips
- ✅ Manage academic calendar
- ✅ Submit and approve leave for teachers
- ✅ View attendance reports
- ✅ Approve student promotions/transfers

**Restricted**:
- ❌ Cannot modify payroll settings
- ❌ Cannot change finance settings
- ❌ Cannot add/remove users

---

### 4. **Teacher**
Manages class and student academic information.

**Dashboard**: Class dashboard with attendance, grades, timetable
**Capabilities**:
- ✅ Mark student attendance
- ✅ Record exam scores
- ✅ View class timetable
- ✅ Submit leave applications
- ✅ View own payslips
- ✅ Message other staff
- ✅ Submit expense requests
- ✅ View student academic records

**Restricted**:
- ❌ Cannot create or modify exams
- ❌ Cannot change student data
- ❌ Cannot access other staff records

---

### 5. **Auxiliary Staff** (Support Staff)
Supports operations (cleaners, security, drivers).

**Dashboard**: Task dashboard with schedules
**Capabilities**:
- ✅ Mark own attendance
- ✅ View own payslips
- ✅ Request leave

**Restricted**:
- ❌ Cannot view academic data
- ❌ Cannot access finance
- ❌ Cannot manage other staff

---

### 6. **Parent**
Access to child's academic progress and communications.

**Dashboard**: Child academic progress and announcements
**Capabilities**:
- ✅ View child's grades and attendance
- ✅ View announcements
- ✅ Receive notifications
- ✅ Pay fees online
- ✅ Message teacher

**Restricted**:
- ❌ Cannot modify any data
- ❌ Cannot access other students
- ❌ Cannot view finance details

---

### 7. **Student**
Access to own academic records and communications.

**Dashboard**: Personal academic dashboard
**Capabilities**:
- ✅ View own grades
- ✅ View own attendance
- ✅ View announcements
- ✅ View timetable
- ✅ Submit assignments (if LMS enabled)

**Restricted**:
- ❌ Cannot modify any data
- ❌ Cannot view other students
- ❌ Cannot access finance

---

## Feature Matrix

### Module Access by Role

| Feature | Admin | Manager | Head Teacher | Teacher | Parent | Student |
|---------|-------|---------|--------------|---------|--------|---------|
| **Staff Management** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Staff Discipline | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Payroll Management | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Allowances/Deductions | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Payslips | ✅ | ✅ | ✅ | ✅ (own) | ❌ | ❌ |
| **Student Management** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Student Discipline | ✅ | ✅ | ✅ | ✅ (report) | ❌ | ❌ |
| Enrollment/Promotion | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Finance** | ✅ | ✅ | ❌ | ✅ (submit) | ❌ | ❌ |
| Create Invoices | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Record Payments | ✅ | ✅ | ❌ | ❌ | ✅ (online) | ❌ |
| Budget Management | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Academics** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create Exams | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Record Scores | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Generate Report Cards | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Own Grades | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Attendance** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| View Attendance | ✅ | ✅ | ✅ | ✅ (own class) | ✅ (own child) | ✅ (own) |
| **Communication** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Send Announcements | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Message Staff | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Analytics** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## Workflows & Processes

### 1. **Staff Promotion Workflow**
```
Teacher submits self-assessment
    ↓
Manager/Head Teacher reviews profile
    ↓
Approves promotion to Head Teacher
    ↓
System updates role and permissions
    ↓
Staff notified of promotion
```

### 2. **Staff Discipline Workflow**
```
Incident Reported (Disciplinary Action created)
    ↓
Status: Reported
    ↓
Under Review (Evidence collected, investigation)
    ↓
Status: Under Review
    ↓
Decision made (Approved/Rejected)
    ↓
Status: Approved/Rejected
    ↓
Action Implemented (Training, Warning, etc.)
    ↓
Status: Implemented/Appealed
```

### 3. **Staff Suspension Workflow**
```
Suspension Request created
    ↓
Manager/Admin reviews
    ↓
Approve suspension dates
    ↓
System tracks:
  - Suspension period
  - Pay during suspension (full/half/none)
  - Benefits status
  - Employee acknowledgement
    ↓
Can be appealed (generates new decision workflow)
    ↓
Lifted after period ends
```

### 4. **Staff Termination Workflow**
```
Termination Request initiated
    ↓
Reason documented (performance, conduct, redundancy, voluntary)
    ↓
System calculates:
  - Last working day
  - Severance entitlement
  - Outstanding leave payout
  - Benefits status
    ↓
Exit Interview scheduled
    ↓
Asset recovery tracking
    ↓
Final settlement
    ↓
Status: Executed
```

### 5. **Student Suspension Workflow**
```
Suspension requested with reason
    ↓
Status: Requested
    ↓
Manager/Head Teacher reviews
    ↓
Status: Under Review (Investigation)
    ↓
Parent notification sent
    ↓
Decision: Approved/Rejected
    ↓
If approved:
  - Suspension start/end dates set
  - Parent confirmation required
  - System marks absences as suspension days
    ↓
Re-entry conditions defined
    ↓
Can be lifted or appealed
```

### 6. **Student Expulsion Workflow**
```
Expulsion recommended with reason
    ↓
Status: Recommended
    ↓
Head Teacher/Manager reviews
    ↓
Status: Under Review
    ↓
Investigation documentation
    ↓
Multi-level approval:
  - Head Teacher approval
  - Manager/District approval
  - Admin final approval
    ↓
Parent meeting recorded
    ↓
Status: Approved
    ↓
Alternative school transfer arranged (if applicable)
    ↓
Status: Executed
```

### 7. **Expense Approval Workflow**
```
Staff submits expense request
    ↓
System determines approval tier based on amount
    ↓
Amount ≤ 10,000
    └→ Route to Head Teacher (Level 1)
Amount 10,001 - 50,000
    └→ Route to Manager (Level 2)
Amount > 50,000
    └→ Route to Admin (Level 3)
    ↓
Approver reviews and decides
    ↓
If approved:
  - Posted to General Ledger
  - Linked to Chart of Accounts
  - Budget updated (spent increased)
    ↓
If rejected:
  - Returned to staff with feedback
```

### 8. **Payroll Processing Workflow**
```
Configure allowances/deductions per employee
    ↓
Monthly: System generates Payroll record
    ↓
Calculate:
  - Gross = Basic + Active Allowances
  - Deductions = Active Deductions (fixed + percentage-based)
  - Net = Gross - Deductions
    ↓
Generate PaySlip with itemized breakdown
    ↓
Manager reviews & approves
    ↓
Issue to employee
    ↓
Employee acknowledges receipt (optional but tracked)
    ↓
Process payment (bank transfer, cash, etc.)
    ↓
Status: Paid
```

### 9. **Leave Application Workflow**
```
Staff submits leave request with dates
    ↓
System checks:
  - Leave balance for type
  - Holiday calendar
  - Other approvals needed
    ↓
Route to Manager/Head Teacher for approval
    ↓
If approved:
  - Mark dates as leave in attendance
  - Deduct from leave balance
  - Send confirmation to staff
    ↓
If rejected:
  - Send denial reason
  - Staff can resubmit different dates
```

### 10. **Fee Payment Workflow**
```
Admin creates FeeInvoice for student
    ↓
Invoice shows:
  - Invoice number
  - Due date
  - Fee components (tuition, registration, meals)
  - Total amount due
    ↓
Parent receives notification
    ↓
Parent pays via:
  - Bank transfer
  - Cash at office
  - Mobile money
  - Card payment
    ↓
Staff records payment with receipt
    ↓
System generates Receipt (formal audit trail)
    ↓
Invoice status updated (partially/fully paid)
    ↓
Arrears tracking updated
```

---

## Database Models

### Core User Model
```python
class User(AbstractBaseUser):
    user_type: str  # admin, manager, head_teacher, teacher, auxiliary, parent, student
    is_active: bool
    onboarding_completed: bool
    reports_to: ForeignKey(User)  # Hierarchical reporting
    first_name, last_name, email
```

### Key Models by Module

#### Administration
- `Staff` (employment details, salary, department)
- `Student` (enrollment, grade, class)
- `ClassRoom` (class structure, teacher assignment)
- `TeacherAssignment` (subject per grade)
- `StaffDisciplinaryAction`, `StaffSuspensionRequest`, `StaffTerminationRequest`
- `StudentSuspension`, `StudentExpulsion`

#### HR
- `LeaveType`, `LeaveApplication`
- `PayrollStructure`, `Payroll`, `PayrollComponent`
- `StaffAllowance`, `StaffDeduction`
- `PaySlip`, `PaySlipAllowance`, `PaySlipDeduction`, `PayslipBatch`
- `PerformanceReview`, `Training`, `TrainingAttendance`
- `Contract`

#### Finance
- `FeeStructure`, `FeeInvoice`, `Payment`, `PaymentReceipt`
- `Expense`, `ExpenseApprovalLevel`, `ExpenseApprovalWorkflow`, `ExpenseApproval`
- `BankAccount`, `ChartOfAccounts`, `GeneralLedgerEntry`
- `BudgetAllocation`, `BankReconciliation`, `BankStatement`, `BankTransaction`

#### Academics
- `Subject`, `Grade`, `Exam`, `ExamScore`
- `TimeTable`, `ReportCard`

#### Attendance
- `StudentAttendance`, `StaffAttendance`

#### Communication
- `Message`, `Announcement`, `EmailTemplate`
- `StudentContact`, `ParentContact`

---

## API & URLs

### Frontend URL Patterns

```
/dashboard/                          # Dashboard router (redirects by role)

# STUDENT MANAGEMENT
/students/                           # Student list
/students/<pk>/                      # Student detail
/students/<pk>/edit/                 # Edit student
/students/register/                  # Register new student

# STAFF MANAGEMENT
/staff/                              # Staff list
/staff/<pk>/                         # Staff detail (with payslips & allowances)
/staff/add/                          # Add new staff
/staff/<pk>/promote/                 # Promote to Head Teacher

# DISCIPLINE
/staff/disciplinary/                 # Staff disciplinary list
/staff/<pk>/disciplinary/report/     # Report disciplinary action
/staff/suspensions/                  # Suspension list
/staff/<pk>/suspend/                 # Create suspension request
/students/suspensions/               # Student suspension list
/students/<pk>/suspend/              # Request student suspension

# PAYROLL MANAGEMENT
/payroll/allowances/                 # List allowances
/payroll/allowances/staff/<id>/add/  # Create allowance
/payroll/deductions/                 # List deductions
/payroll/deductions/staff/<id>/add/  # Create deduction
/payroll/payslips/                   # List payslips
/payroll/payslips/<pk>/              # Payslip detail
/payroll/staff/<id>/payslip-history/ # Staff payslip history
/payroll/batches/                    # Payslip batch list

# FINANCE
/financial/                          # Finance dashboard
/financial/income/                   # Income list
/financial/expenses/                 # Expense list
/finance/invoices/                   # Fee invoices
/finance/payments/                   # Payment recording
/finance/accounts/                   # Student accounts

# ACADEMICS
/academics/                          # Academics home
/academics/exams/                    # Exam management
/academics/exams/<pk>/scores/        # Score entry
/academics/timetable/                # Timetable view
/academics/calendar/                 # Academic calendar

# ATTENDANCE
/attendance/                         # Mark attendance
/attendance/summary/                 # Attendance reports

# ANALYTICS
/analytics/                          # Analytics dashboard
```

### Django Admin URLs
- Admin interface available at `/admin/`
- All models registered in respective `admin.py` files
- Customized list displays and filters per model

---

## Setup & Deployment

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (venv/virtualenv)
- Database (SQLite for dev, PostgreSQL recommended for production)

### Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd jds_system

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create database
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Load sample data (if available)
python manage.py loaddata sample_data.json

# 7. Run development server
python manage.py runserver
```

### Configuration
**File**: `backend/school_management/settings.py`

Key settings:
- `INSTALLED_APPS`: All Django apps
- `DATABASES`: Database configuration
- `EMAIL_BACKEND`: Email configuration
- `ALLOWED_HOSTS`: Allowed domain names
- `STATIC_ROOT`, `MEDIA_ROOT`: File storage

### Database Initialization

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Deployment (Production)

```bash
# Generate static files
python manage.py collectstatic

# Use gunicorn/uWSGI for app server
gunicorn school_management.wsgi:application

# Use nginx as reverse proxy
# Use PostgreSQL for database
# Enable HTTPS/SSL
# Set DEBUG = False
```

### Sample Data Import

```bash
# Export current data
python manage.py dumpdata > backup.json

# Import sample data
python manage.py loaddata sample_student_import.csv  # For CSV imports
```

---

## System Features Summary

### ✅ Implemented Features
- [x] Multi-role user authentication and RBAC
- [x] Staff management with promotion workflows
- [x] Student enrollment and management
- [x] Staff discipline with approval workflows
- [x] Student discipline (suspension/expulsion)
- [x] Payroll with allowances and deductions
- [x] Payslip generation and batch processing
- [x] Leave application and approval
- [x] Finance management (invoicing, payments)
- [x] Expense tracking with multi-tier approvals
- [x] Academic exam and grading
- [x] Attendance tracking
- [x] General ledger and chart of accounts
- [x] Budget allocation and tracking
- [x] Bank reconciliation
- [x] Communication and announcements

### 🔄 In Progress / Next Phase
- [ ] Online fee payment integration
- [ ] Advanced analytics and forecasting
- [ ] Mobile app
- [ ] Learning management system (LMS)
- [ ] Parent/Student portals (full implementation)
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Advanced reporting (PDF generation)

### 📋 Roadmap
- Complete LMS module
- Implement portals for parents/students
- Add mobile authentication
- Enhanced analytics with forecasting
- Document management system
- Timetable scheduling optimization
- Integration with payment gateways

---

## Support & Maintenance

### Database Backups
```bash
# Backup SQLite
cp backend/db.sqlite3 backups/db.sqlite3.backup

# Backup PostgreSQL
pg_dump school_db > backup.sql
```

### Troubleshooting

**Issue**: Migration conflicts
```bash
python manage.py showmigrations
python manage.py migrate <app> <migration-name>
```

**Issue**: Static files not loading
```bash
python manage.py collectstatic --clear --noinput
```

**Issue**: Database locked
```bash
# Close all connections and restart server
python manage.py dbshell
.quit
python manage.py migrate
```

### Documentation
- See individual module `models.py` files for detailed model documentation
- See individual `views.py` files for view logic documentation
- See `README.md` for quick start guide

---

## Author
**JDS School Management System Development Team**

## License
Proprietary - All Rights Reserved

## Version
v1.0.0 (Initial Release)

---

**Last Updated**: 2024
**System Status**: Production Ready ✅
