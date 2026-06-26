# Current System Features and Capabilities

## Overview

This document captures the current state of the School Management System as implemented in the codebase, including the major modules that are already available, the workflows they support, and the next steps needed to move the platform from a strong operational core into a polished, enterprise-grade school operating system.

The system is built with Django 6.0 and is structured as a multi-module school platform that supports administration, academics, finance, communication, attendance, LMS, HR, inventory, transport, security, portals, analytics, and synchronization. The current design is aimed at an offline-first desktop deployment with role-based access, while keeping a path open for future web portal expansion.

## Verified Live Flows

Browser validation against the running app confirmed the following user-facing flows:
- Authentication: seeded admin login works and opens the authenticated dashboard shell.
- Navigation: the sidebar exposes the main module groups and the notification icon is present in the header area.
- Approvals: `/manager/approvals/` renders a unified approval inbox with search, type filtering, status filtering, and separate tabs for restocking and student edit requests.
- Notifications: `/notifications/` renders a dedicated inbox page.
- Academics: `/academics/exams/` loads successfully and supports exam creation from the page.
- Attendance: `/attendance/` loads successfully and supports date/class filtering plus attendance marking.
- Finance: `/finance/invoices/` loads successfully and exposes invoice metrics, search, and invoice generation actions.
- Communication: `/communication/announcements/` loads successfully and exposes forms for announcements, messages, reminders, newsletters, and appointment requests.
- Students: `/students/` loads successfully and exposes search, filters, detail, edit, registration, promotion, transfer, and export actions.
- Staff: `/staff/` loads successfully and exposes staff search, filters, detail pages, and profile completion actions.

What this means in practice:
- The platform is not just wired for module routing; several key screens are already interactive and populated with real empty states and approval data.
- The most complete cross-department workflow currently visible in the UI is the approvals/notifications path.
- The current test data is sparse in some modules, so some pages appear as clean empty states rather than populated operational views.

## Current Platform Capabilities

### 1. Identity, Roles, and Access Control

The platform uses a custom user model with a `user_type` field to separate the experience for each category of person in the school ecosystem.

Supported user types currently include:
- Administrator
- Manager
- Head Teacher
- Teacher
- Auxiliary Staff
- Parent
- Student

Current identity-related capabilities:
- Role-based login routing
- Custom user profiles with contact information and onboarding fields
- Reporting relationships through `reports_to` for hierarchy management
- Staff and student-specific profile models
- Portal access controls for parents and students
- Security and audit-focused module separation

What this enables in practice:
- Different dashboards for different roles
- Role-specific navigation and permissions
- Separation of financial, academic, and administrative workflows
- Controlled access to sensitive records

### 2. Administration Module

The administration module is the operational backbone of the system.

Current capabilities include:
- Student registration and profile management
- Staff registration and profile management
- Grade and class structure management
- Academic year and term setup
- School information configuration
- Student transfer and promotion flows
- Staff onboarding invite and completion flow
- Document collection for staff onboarding

Student management supports:
- Admission number tracking
- Current class assignment
- Guardian and parent data
- Personal and medical details
- Active/inactive status handling

Staff management supports:
- Staff type classification
- Employment data
- Designation, qualification, and experience
- Onboarding completion tracking
- Identity and documentation capture

The current onboarding model supports:
- Token-based invitation flow
- Profile completion tracking
- Document uploads such as NRC and other supporting files
- Manager/admin-driven completion actions

### 3. Academics Module

The academics module currently supports curriculum, assessment, schedules, and reporting.

Available academic capabilities:
- Subject management
- Subject allocation to grades/classes
- Syllabus records
- Assignment creation and submission tracking
- Exam creation and scheduling
- Exam results and score entry
- Report card generation
- Report card editing for authorized roles
- Grading and performance evaluation
- Timetable support for day-to-day class planning
- Calendar support for school events and term planning

Assessment-related workflows:
- Create exams for a subject and class
- Enter or update student scores
- Automatically compute grades from marks
- Generate report cards per term
- Store attendance-linked academic summaries

Timetable capability:
- A real timetable model now exists
- Stores class, subject, teacher, term, academic year, day of week, start time, and end time
- Supports direct rendering of daily schedules in the frontend

Calendar capability:
- Uses the school event calendar model
- Supports holidays, meetings, sports, cultural events, workshops, and parent-teacher meetings
- Can be filtered and presented as a school-wide planning view

### 4. Finance Module

Finance is one of the most developed modules in the platform.

Current financial capabilities:
- Fee structure management
- Invoice generation
- Payment recording
- Receipt generation
- Student account statement views
- Arrears tracking
- Reminder support
- Expense recording
- Financial dashboards and summaries

Fee structure support includes:
- Grade-based fee mapping
- Academic-year scoping
- Compulsory and optional charges
- Payment frequency definition
- Fee amount storage

Invoice workflows include:
- Bulk invoice generation for selected grades or classes
- Individual invoice creation
- Balance tracking
- Due date handling
- Status tracking such as pending, partial, paid, and overdue

Payment workflows include:
- Payment capture per invoice
- Payment method and reference tracking
- Automatic balance updates
- Receipt number generation
- PDF receipt generation support

Accounts and arrears features include:
- Outstanding balance summaries by student
- Grade-level debt analysis
- Aging analysis for overdue fees
- Finance overview dashboards for bursar and management views

### 5. Communication Module

The communication module supports internal and external school communication.

Current communication capabilities:
- Announcements
- Direct messages
- Newsletters
- Email logs
- SMS logs
- Appointment requests
- Communication hub for creating and routing multiple communication types

The communication hub supports:
- Announcements for school-wide notices
- Internal messages between users
- Reminder queueing for staff, parents, or students
- Newsletter drafting and publishing
- Appointment request submission for meetings

Appointment support currently enables:
- Parent or other user initiation of a meeting request
- Target staff selection
- Subject, details, preferred date, preferred time, duration, and location capture

### 6. Attendance Module

Attendance is currently implemented for both students and staff.

Existing attendance capabilities:
- Student daily attendance
- Staff attendance
- Attendance summaries
- Discipline incident tracking
- Behavior logging

This allows the school to:
- Monitor daily presence
- Review attendance trends
- Link behavior and discipline records to student history
- Feed attendance data into report cards and dashboards

### 7. LMS Module

The learning management module provides a foundation for digital academic content delivery.

Current LMS capabilities:
- Course creation
- Lesson content storage
- Lesson progress tracking
- Online quiz creation and attempts
- Discussion forums
- Forum posts and replies

This gives the platform the ability to grow into:
- Blended learning
- Homework and reading management
- Teacher-led digital class content
- Online formative assessments

### 8. HR Module

The HR module supports staff lifecycle management.

Current HR capabilities:
- Leave types and applications
- Leave approval workflow
- Payroll structure components
- Monthly payroll processing
- Performance reviews
- Training programs
- Training attendance tracking
- Employment contracts

This module is a foundation for:
- Staff administration
- Payroll governance
- Workforce planning
- HR compliance records

### 9. Inventory Module

Inventory management is included for physical school assets and supplies.

Current inventory capabilities:
- Item categorization
- Inventory item tracking
- Stock transactions
- Asset assignment
- Maintenance scheduling
- Maintenance record tracking

This can be used for:
- Food supplies
- Teaching materials
- Office assets
- Maintenance and repair logs

### 10. Transport Module

Transport is supported for school bus and route operations.

Current transport capabilities:
- Vehicle management
- Driver management
- Route planning
- Student transport assignments
- Trip logging
- Vehicle maintenance records
- Fuel tracking

This supports:
- Daily transport planning
- Student pickup coordination
- Fleet management
- Route accountability

### 11. Security Module

Security is treated as a first-class operational concern.

Current security capabilities:
- Custom user roles
- Role-based permissions
- User role assignments
- Audit logging for CRUD actions
- Access logging for login/logout events
- Backup tracking
- Compliance documentation records
- Security incident reporting

This provides:
- Better accountability
- Visibility into access and changes
- A base for future compliance workflows

### 12. Portals Module

Portal support is already present for future-facing user experiences.

Current portal capabilities:
- Student portal access control
- Parent portal access control
- Portal notifications
- Event calendar support
- Feedback system

This creates a route toward:
- Parent self-service views
- Student academic access
- Notification delivery
- Controlled external access

### 13. Analytics Module

Analytics support is included for operational reporting and decision-making.

Current analytics capabilities:
- Performance trend analysis
- Attendance trend tracking
- Financial dashboards
- Enrollment trend analysis
- Teacher workload analysis
- Discipline analytics
- Custom report generation

This enables leadership to monitor:
- Academic performance over time
- Attendance risk patterns
- Revenue and arrears trends
- Staff workload distribution

### 14. Sync Module

The sync layer is already modeled to support offline-first deployment.

Current sync capabilities:
- Sync logs
- Pending sync queue
- Conflict records
- Device registration
- Sync settings

This is the foundation for:
- Offline data capture
- Future cloud reconciliation
- Device-aware deployments
- Reliable sync conflict handling

## Frontend and Navigation Status

The frontend has progressed from basic screens to a more structured dashboard experience.

Current frontend capabilities:
- Base frontend layout with grouped navigation
- Dashboard routing by user type
- Finance pages for invoices, payments, fee structures, accounts, arrears, and expenses
- Academic pages for exams, results, timetable, calendar, and report cards
- Staff onboarding pages
- Communication hub page
- Student and staff listing pages

Recent navigation improvements include:
- Grouped sidebar sections for Academics, Students, Finance, Employees, Operations, and Communication
- Direct access to timetable and calendar views
- More role-specific entry points for management and teaching workflows

## Default Role Accounts Seeded in the Database

The system now includes seeded role accounts with password `1234` for initial access and testing.

Seeded accounts:
- Manager
- HeadTeacher
- Teacher
- Auxilery
- Parent
- Student

Purpose of these accounts:
- Immediate role testing
- UI verification across different dashboards
- Permission checks for finance, academics, and communication features
- Faster onboarding during development and demonstrations

## Current Strengths

The strongest parts of the platform right now are:
- A broad domain model already in place
- A complete role-based user structure
- Finance workflows that already go beyond simple CRUD
- Academic reporting that supports score entry and report cards
- Communication and appointment coordination
- Offline-first sync planning
- A growing frontend with real task-oriented pages

## What Still Needs Work

Although the core platform is functional, several areas still need refinement.

Current gaps and rough edges:
- Some pages still use placeholder or minimal layouts
- Not every feature has a full CRUD frontend yet
- Some modules are stronger in models than in user workflows
- The timetable and calendar experience needs richer data entry screens
- Reporting can be expanded with more exports and printable views
- Parent portal capabilities are still limited compared to staff workflows
- Sync remains modeled, but the operational sync commands and background logic still need completion

## Next Steps

### 1. Build Full Timetable Management UI

Add complete CRUD views for timetable entries.

Recommended work:
- List timetable entries by class, teacher, and day
- Add form-based creation and editing
- Add validation for overlapping periods
- Support copying schedules across terms or academic years
- Add teacher and classroom conflict checks
- Provide printable timetable views for staff and students

### 2. Expand Calendar Management

Turn the calendar into a full planning tool.

Recommended work:
- Add event creation and editing screens
- Support term events, holidays, exams, meetings, and school closures
- Add public/private visibility flags
- Provide filters by date range and event type
- Add calendar cards or timeline views instead of table-only rendering

### 3. Complete Finance Workflows

Finance is functional, but the user experience can be improved substantially.

Recommended work:
- Add better invoice creation forms
- Add payment search and filtering
- Add aged arrears dashboards
- Add printable statements for parents and management
- Add fee structure duplication across academic years
- Add bulk reminder sending with templates

### 4. Polish Report Cards

Report cards are generated, but the workflow can be made more complete.

Recommended work:
- Add class ranking and subject-level summaries
- Add printable PDF output
- Add comments workflow for class teachers and principals
- Add per-term archive browsing
- Add editable moderation controls with approval logging

### 5. Improve Communication and Appointment Handling

The communication layer should become a proper collaboration hub.

Recommended work:
- Add appointment approval or rejection workflow
- Add communication inbox/outbox views
- Add parent-teacher meeting scheduling pages
- Add message read/unread states and search
- Add notification badges in the sidebar and dashboard

### 6. Build the Parent Portal

The external portal should become a polished self-service experience.

Recommended work:
- Parent login and child linking flow
- Results viewing pages
- Attendance summaries
- Fee balance and payment history views
- Announcements and calendar access
- Communication request forms

### 7. Expand Analytics

Analytics should evolve from summary counters into operational insight.

Recommended work:
- Charts for attendance, fees, and performance
- Drill-down by class, term, subject, and teacher
- Exportable reports in PDF and Excel
- Trend detection for arrears and absences
- Head-teacher and manager dashboard widgets

### 8. Finish Offline Sync

The sync architecture is modeled, but operational behavior still needs implementation.

Recommended work:
- Build sync push and pull commands
- Add background sync jobs
- Add conflict resolution screens
- Add device registration workflow
- Add last-sync status indicators per device

### 9. Modernize the UI

The frontend should move from functional to polished.

Recommended work:
- Improve typography and visual hierarchy
- Add richer dashboard cards and chart blocks
- Make all core pages responsive for smaller screens
- Introduce more intentional spacing and iconography
- Add success, warning, and empty-state styling patterns

### 10. Add Operational Utilities

There are several practical utilities that will make the system easier to operate.

Recommended work:
- Import/export for students, staff, and fee structures
- Bulk class promotion tools
- Bulk invoice generation workflows
- Backup and restore UI
- Email and SMS provider integrations
- Better admin bootstrap and demo-data tooling

## Suggested Priority Order

1. Finish timetable and calendar management screens.
2. Strengthen finance workflows and report outputs.
3. Improve parent-facing portal access.
4. Add richer analytics and printable reports.
5. Complete offline sync and device workflows.
6. Upgrade the overall frontend polish.

## Summary

The current codebase already represents a substantial school management platform rather than a bare scaffold. The main business domains are present, the database is structured, the dashboards exist, and the most important workflows are operational. The next phase should focus on tightening the user experience, completing missing CRUD surfaces, and turning the modeled capabilities into polished end-user workflows.
