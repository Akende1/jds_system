# School Management System
**Version:** 1.0.0 (Desktop + Web Ready)  
**Status:** ✅ Core System Operational | 🔄 UI Modernization In Progress

A comprehensive Django-based School Management System designed for **offline-first desktop deployment** with cloud synchronization capabilities, plus a future web portal for parents.

> **📖 NEW: Comprehensive System Documentation**  
> For complete system documentation including all modules, workflows, user roles, feature matrix, and setup instructions, see [README_SYSTEM.md](README_SYSTEM.md).

---

## 🎯 **System Architecture**

### **Desktop Application** (Primary - For School Staff)
- 💻 **Target Users**: School Administrators, Teachers, Principals, Office Staff
- 🔌 **Offline-First**: Full functionality without internet connection
- 🔄 **Cloud Sync**: Automatic synchronization when online
- 📦 **Deployment**: Electron-wrapped Django app (planned)
- 🔐 **Security**: Device registration with role-based access

### **Web Application** (Future - For Parents)
- 🌐 **Target Users**: Parents and Guardians
- 📱 **Features**: View results, make payments, check attendance
- 🔒 **Access**: Online-only, read-focused portal

---

## ✅ **What's Working (Fully Operational)**

### **1. Core Infrastructure** ✅
- ✅ Django 6.0 backend running successfully
- ✅ SQLite database with complete schema (100+ models)
- ✅ All 13 modules installed and migrated
- ✅ Admin interface fully functional
- ✅ Zero system check errors
- ✅ Authentication system operational

### **2. Sync Module** ✅ NEW!
- ✅ **SyncLog**: Track all synchronization operations
- ✅ **PendingSync**: Queue for offline changes (create/update/delete)
- ✅ **SyncConflict**: Conflict detection and resolution
- ✅ **DeviceRegistration**: Manage multiple desktop installations
- ✅ **SyncSettings**: Per-device sync configuration (auto/manual/scheduled)
- ✅ Database migrations completed
- ✅ Admin interface configured

### **3. Administration Module** ✅
- ✅ User management (Students, Staff, Parents, Admins)
- ✅ Student registration with admission numbers
- ✅ Staff management (Teachers, Admin, Auxiliary)
- ✅ Class and grade management
- ✅ Academic year and term structures
- ✅ School information settings
- ✅ Views: Dashboard, Student List/Detail, Staff List/Detail

### **4. Academics Module** ✅
- ✅ Subject management
- ✅ Subject allocation to grades
- ✅ Syllabus tracking
- ✅ Assignment creation and submission
- ✅ Exam scheduling
- ✅ Exam results and grading
- ✅ Report card generation
- ✅ Grading schemes

### **5. Finance Module** ✅
- ✅ Fee structures and categories
- ✅ Monthly billing (Tuition, Lunch, Transport)
- ✅ Automated invoice generation
- ✅ Payment recording with auto-receipt numbers (RCP-YYYY-XXXXXX)
- ✅ Payment reminders (Soft/Final/Exam Blacklist)
- ✅ Arrears tracking (4-tier aging: 0-30, 31-60, 61-90, 90+ days)
- ✅ Discount management
- ✅ Expense tracking

### **6. Communication Module** ✅
- ✅ Announcement system with priority levels
- ✅ Direct messaging between users
- ✅ Newsletter management
- ✅ SMS logging
- ✅ Email logging
- ✅ Parent-teacher communication records

### **7. Attendance Module** ✅
- ✅ Student daily attendance tracking
- ✅ Staff attendance tracking
- ✅ Attendance summaries (monthly aggregation)
- ✅ Discipline incident management
- ✅ Behavior logging (positive/negative points)

### **8. LMS (Learning Management)** ✅
- ✅ Course creation and management
- ✅ Lesson content (video, documents, presentations)
- ✅ Lesson progress tracking
- ✅ Online quizzes
- ✅ Quiz attempts and grading
- ✅ Discussion forums
- ✅ Forum posts and replies

### **9. HR (Human Resources)** ✅
- ✅ Leave types and applications
- ✅ Leave approval workflow
- ✅ Payroll structure components
- ✅ Monthly payroll processing
- ✅ Performance reviews
- ✅ Training programs
- ✅ Training attendance tracking
- ✅ Employment contracts

### **10. Inventory Module** ✅
- ✅ Item categorization
- ✅ Inventory item tracking
- ✅ Stock transactions (purchase, issue, return, adjustment)
- ✅ Asset assignment to staff/students
- ✅ Maintenance scheduling
- ✅ Maintenance record tracking

### **11. Transport Module** ✅
- ✅ Vehicle management
- ✅ Driver information
- ✅ Route planning
- ✅ Student transport assignments
- ✅ Trip logging
- ✅ Vehicle maintenance records
- ✅ Fuel tracking

### **12. Security Module** ✅
- ✅ Custom user roles
- ✅ Role-based permissions
- ✅ User role assignments
- ✅ Audit logging (all CRUD operations)
- ✅ Access logs (login/logout tracking)
- ✅ Data backup tracking
- ✅ Compliance document management
- ✅ Security incident reporting

### **13. Portals Module** ✅
- ✅ Student portal access controls
- ✅ Parent portal access controls
- ✅ Portal notifications
- ✅ Event calendar
- ✅ Feedback system

### **14. Analytics Module** ✅
- ✅ Performance trend analysis
- ✅ Attendance trend tracking
- ✅ Financial dashboards
- ✅ Enrollment pattern analytics
- ✅ Teacher workload analysis
- ✅ Discipline analytics
- ✅ Custom report generation

---

## 🔄 **What's In Progress**

### **Frontend UI/UX** 🔄
- ✅ Base template with Bootstrap 5
- ✅ Login page
- ✅ Dashboard (basic statistics)
- ✅ Student list and detail pages
- ✅ Staff list and detail pages
- 🔄 **Needs Modernization**:
  - Enhanced dashboard with charts
  - Modern card-based layouts
  - Responsive mobile design
  - Dark mode support
  - Better form styling
  - Advanced search/filtering UI

### **Additional Views Needed** 🔄
- 🔄 Exam management pages
- 🔄 Payment collection interface
- 🔄 Attendance marking interface
- 🔄 Report card generation UI
- 🔄 Fee invoice management
- 🔄 SMS/Email composition
- 🔄 Analytics dashboards with charts

---

## ❌ **What's Not Implemented Yet**

### **Desktop App Packaging** ❌
- ❌ Electron wrapper configuration
- ❌ Auto-updater system
- ❌ Native installers (.exe for Windows, .dmg for macOS)
- ❌ Device registration flow UI
- ❌ Offline detection and sync triggers

### **Sync Implementation** ❌
- ❌ Management commands (`sync_push`, `sync_pull`, `sync_full`)
- ❌ Django signals for auto-tracking changes
- ❌ Background sync service
- ❌ Conflict resolution UI
- ❌ Cloud database setup (PostgreSQL/MySQL)
- ❌ Sync API endpoints

### **Parent Web Portal** ❌
- ❌ Parent-specific authentication
- ❌ Results viewing interface
- ❌ Fee payment interface
- ❌ Online payment gateway integration
- ❌ Mobile-responsive views

### **Reporting** ❌
- ❌ PDF report generation (ReportLab integration)
- ❌ Excel export functionality
- ❌ Automated report scheduling
- ❌ Email report delivery

### **Advanced Features** ❌
- ❌ Bulk operations (bulk student registration, bulk fee generation)
- ❌ Data import/export (CSV, Excel)
- ❌ SMS gateway integration
- ❌ Email SMTP configuration
- ❌ Backup/restore functionality
- ❌ Multi-school support (if needed)

---

## 📊 **System Status Summary**

| Component | Status | Progress |
|-----------|--------|----------|
| **Backend Models** | ✅ Complete | 100% |
| **Database Migrations** | ✅ Complete | 100% |
| **Admin Interface** | ✅ Complete | 100% |
| **Sync Infrastructure** | ✅ Complete | 100% |
| **Core Views** | ✅ Basic | 40% |
| **Templates** | 🔄 Basic | 30% |
| **Modern UI** | 🔄 In Progress | 20% |
| **Sync Commands** | ❌ Not Started | 0% |
| **Desktop App** | ❌ Not Started | 0% |
| **Parent Portal** | ❌ Not Started | 0% |

---

## 🎯 Features

### 1. **Administration Core**
- Student registration and management
- Staff/Employee management (Managers, Head Teachers, Teachers, Auxiliary Staff)
- Class allocations
- Academic calendar and term structures
- Grade management
- School information

### 2. **Academics & Curriculum**
- Subject management
- Syllabus tracking
- Assignment creation and submission
- Examinations and assessments
- Grading schemes
- Report cards generation

### 3. **Finance & Billing**
- Fee structures
- Invoice generation
- Payment tracking
- Arrears management
- Discounts and scholarships
- Expense tracking
- Financial reports

### 4. **Communication & Engagement**
- Announcements system
- Newsletters
- Direct messaging
- SMS/Email integration
- Parent-Teacher communication logs

### 5. **Attendance & Discipline**
- Student and staff attendance tracking
- Punctuality logs
- Discipline incident management
- Behavior analytics
- Monthly attendance summaries

### 6. **Learning Management System (LMS)**
- E-learning courses
- Lesson management (video, documents, presentations)
- Online quizzes
- Progress tracking
- Discussion forums

### 7. **Human Resources**
- Staff contracts management
- Leave applications
- Payroll processing
- Performance reviews
- Training and development programs

### 8. **Inventory & Assets**
- Equipment and supplies tracking
- Stock transactions
- Asset assignments
- Maintenance schedules
- Condition tracking

### 9. **Transport & Logistics**
- Vehicle management
- Driver management
- Route planning
- Student transport assignments
- Trip logs and tracking
- Vehicle maintenance records

### 10. **Security & Compliance**
- User roles and permissions
- Audit trails
- Access logs
- Data backup tracking
- Compliance documents
- Security incident management

### 11. **Parent & Student Portals**
- Portal access control
- Results viewing
- Fee information
- Attendance tracking
- Assignment submissions
- Event calendar

### 12. **Reporting & Analytics**
- Performance trends
- Attendance analytics
- Financial dashboards
- Enrollment patterns
- Teacher workload analysis
- Discipline analytics
- Custom report generation

---

## 🛠️ **Technology Stack**

### **Backend**
- **Framework**: Django 6.0
- **Language**: Python 3.13.1
- **Database**: SQLite (local/offline) → PostgreSQL/MySQL (cloud sync)
- **ORM**: Django ORM with 100+ models

### **Frontend**
- **CSS Framework**: Bootstrap 5.3
- **Icons**: Font Awesome 6.4
- **JavaScript**: jQuery 3.7
- **Charts**: Chart.js (planned for analytics)

### **Python Packages**
```txt
Django==6.0
Pillow==11.0.0
django-crispy-forms==2.3
crispy-bootstrap5==2025.6
python-decouple==3.8
django-filter==24.3
reportlab==4.2.5
openpyxl==3.1.5
django-widget-tweaks==1.5.0
```

### **Planned Desktop Stack**
- **Wrapper**: Electron
- **Packaging**: electron-builder
- **Auto-Update**: electron-updater
- **Local Server**: Django development server (bundled)

---

## 📦 **Installation & Setup**

### **Prerequisites**
- ✅ Python 3.13+ installed
- ✅ pip package manager
- ✅ Virtual environment support
- ✅ 500MB+ free disk space

### **Quick Start (Development)**

```powershell
# 1. Navigate to project directory
cd C:\Users\rival\Documents\jds_system

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Install dependencies (if not already installed)
pip install -r requirements.txt

# 4. Navigate to backend
cd backend

# 5. Run migrations (if first time)
python manage.py migrate

# 6. Create superuser (if not created)
python manage.py createsuperuser

# 7. Start server
python manage.py runserver

# 8. Access application
# Dashboard: http://127.0.0.1:8000/
# Admin: http://127.0.0.1:8000/admin/
```

### **Current Login Credentials**
Use the superuser account you created with `createsuperuser` command.

---

## 📁 **Project Structure**

```
jds_system/
├── backend/                        # Django backend
│   ├── school_management/          # Main project settings
│   │   ├── settings.py             # Configuration
│   │   ├── urls.py                 # URL routing
│   │   └── wsgi.py                 # WSGI config
│   ├── administration/             # Core admin module ✅
│   ├── academics/                  # Academic management ✅
│   ├── finance/                    # Finance & billing ✅
│   ├── communication/              # Communication tools ✅
│   ├── attendance/                 # Attendance tracking ✅
│   ├── lms/                        # Learning Management ✅
│   ├── hr/                         # Human Resources ✅
│   ├── inventory/                  # Inventory tracking ✅
│   ├── transport/                  # Transport logistics ✅
│   ├── security/                   # Security & audit ✅
│   ├── portals/                    # User portals ✅
│   ├── analytics/                  # Analytics & reports ✅
│   ├── sync/                       # Offline sync module ✅ NEW!
│   ├── manage.py                   # Django CLI
│   └── db.sqlite3                  # SQLite database
├── templates/                      # HTML templates
│   ├── base.html                   # Base template ✅
│   ├── registration/               # Auth templates
│   │   └── login.html              ✅
│   ├── administration/             # Admin templates
│   │   ├── dashboard.html          ✅
│   │   ├── student_list.html       ✅
│   │   ├── student_detail.html     ✅
│   │   ├── staff_list.html         ✅
│   │   └── staff_detail.html       ✅
│   ├── academics/                  # Academic templates 🔄
│   ├── finance/                    # Finance templates 🔄
│   └── attendance/                 # Attendance templates 🔄
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css               # Custom CSS ✅
│   ├── js/
│   │   └── main.js                 # Custom JS ✅
│   └── images/                     # Images
├── venv/                           # Virtual environment
├── requirements.txt                # Python dependencies ✅
├── sample_student_import.csv       # Sample CSV for bulk import ✅
├── README.md                       # This file ✅
├── FEATURES_COMPLETE.md            # Complete feature documentation ✅
├── CLEANUP_SUMMARY.md              # Codebase cleanup log ✅
├── DESKTOP_SYNC_ARCHITECTURE.md    # Sync architecture docs ✅
├── EMAIL_CONFIGURATION_GUIDE.md    # SMTP setup guide ✅
├── REPORT_SCHEDULING_GUIDE.md      # Report automation guide ✅
└── QUICKSTART.md                   # Quick setup instructions ✅
```

---

## 🚀 **Usage Guide**

### **1. First-Time Setup**

#### **A. Create Academic Structure**
```
Admin Panel → Administration
1. Create Academic Year (e.g., 2024/2025)
2. Create Terms (e.g., Term 1, Term 2, Term 3)
3. Create Grades (e.g., Grade 1, Grade 2, etc.)
4. Create Class Rooms (e.g., Grade 1A, Grade 1B)
```

#### **B. Add Users**
```
Admin Panel → Administration → Users
1. Create staff users (user_type: teacher/admin/manager)
2. Create student users (user_type: student)
3. Create parent users (user_type: parent)
```

#### **C. Register Students**
```
Admin Panel → Administration → Students
1. Create student profile (links to user)
2. Assign admission number (auto-generated)
3. Assign to class
4. Add parent contact information
```

#### **D. Set Up Finance**
```
Admin Panel → Finance
1. Create Fee Categories (Tuition, Transport, Lunch)
2. Create Fee Structures for each grade
3. Generate monthly invoices (can be automated)
```

#### **E. Configure Subjects**
```
Admin Panel → Academics → Subjects
1. Create subjects (Math, English, Science, etc.)
2. Allocate subjects to grades
3. Assign teachers to subjects
```

### **2. Daily Operations**

#### **Mark Attendance**
```
Admin Panel → Attendance → Student Attendance
- Select date and class
- Mark each student (Present/Absent/Late/Sick/Excused)
```

#### **Record Payments**
```
Admin Panel → Finance → Payments
- Select student
- Select invoice
- Enter amount
- Receipt auto-generated
```

#### **Create Assignments**
```
Admin Panel → Academics → Assignments
- Select subject and class
- Set due date
- Upload attachment (optional)
```

#### **Schedule Exams**
```
Admin Panel → Academics → Exams
- Select subject, class, term
- Set exam date and time
- Add instructions
```

### **3. Reporting**

#### **View Dashboard**
```
http://127.0.0.1:8000/
- Total students, staff, classes
- Fee collection statistics
- Recent registrations
- Today's attendance
```

#### **Generate Reports**
```
Admin Panel → Analytics
- Performance trends
- Attendance analytics
- Financial dashboards
- Custom reports
```

---

## 🔐 **Security Features**

### **Implemented** ✅
- ✅ User authentication and authorization
- ✅ Role-based access control (Admin, Teacher, Student, Parent)
- ✅ Password hashing (Django default)
- ✅ CSRF protection
- ✅ Audit logging (all critical operations)
- ✅ Access logs (login/logout tracking)
- ✅ Session management

### **Recommended for Production** ⚠️
- ⚠️ Enable HTTPS (SSL/TLS)
- ⚠️ Set DEBUG = False
- ⚠️ Use strong SECRET_KEY
- ⚠️ Configure ALLOWED_HOSTS
- ⚠️ Set up proper database backups
- ⚠️ Enable two-factor authentication (2FA)
- ⚠️ Rate limiting for API endpoints
- ⚠️ Regular security audits

---

---

## 🗺️ **Development Roadmap**

### **Phase 1: Backend Completion** ✅ (DONE)
- [x] Fix all admin field errors (93+ errors resolved)
- [x] Create sync module with 5 models
- [x] Apply all database migrations
- [x] Register all models in admin panel
- [x] Test zero system check errors

### **Phase 2: Frontend Enhancement** 🔄 (IN PROGRESS)
- [ ] Modernize UI with Bootstrap 5 components
- [ ] Add dark mode toggle
- [ ] Create responsive mobile layouts
- [ ] Implement Chart.js dashboards
- [ ] Build all missing view templates:
  - [ ] Exam management interface
  - [ ] Payment collection UI
  - [ ] Attendance marking interface
  - [ ] Report card generation
  - [ ] Fee invoice dashboard
  - [ ] SMS/Email composition tool
- [ ] Add loading spinners and progress indicators
- [ ] Implement AJAX for dynamic updates
- [ ] Add data tables with search/filter/export

### **Phase 3: Sync Implementation** ❌ (NOT STARTED)
- [ ] Create management commands:
  - [ ] `sync_push` - Upload local changes
  - [ ] `sync_pull` - Download remote changes
  - [ ] `sync_full` - Bidirectional sync
  - [ ] `resolve_conflicts` - Manual conflict resolution
  - [ ] `register_device` - Device registration
- [ ] Implement Django signals for auto-tracking
- [ ] Build background sync service
- [ ] Add conflict detection and resolution
- [ ] Create sync status UI dashboard
- [ ] Add offline mode indicator

### **Phase 4: Desktop App** ❌ (NOT STARTED)
- [ ] Set up Electron project structure
- [ ] Embed Django server in Electron
- [ ] Create native installers (.exe, .dmg, .deb)
- [ ] Implement device registration flow
- [ ] Add auto-update functionality
- [ ] Build system tray integration
- [ ] Add offline/online status monitoring
- [ ] Create desktop-specific UI enhancements

### **Phase 5: Cloud Deployment** ❌ (NOT STARTED)
- [ ] Set up PostgreSQL/MySQL database
- [ ] Configure cloud hosting (AWS/Azure/DigitalOcean)
- [ ] Create sync API endpoints
- [ ] Implement device authentication
- [ ] Set up automated backups
- [ ] Add monitoring and alerting
- [ ] Configure load balancing
- [ ] Enable HTTPS with SSL certificates

### **Phase 6: Parent Portal** ❌ (NOT STARTED)
- [ ] Parent authentication system
- [ ] Results viewing interface
- [ ] Fee payment integration (Stripe/PayPal)
- [ ] Announcement notifications
- [ ] Mobile app (React Native/Flutter)
- [ ] SMS/Email alerts for grades/fees
- [ ] Online parent-teacher messaging

---

## 🐛 **Troubleshooting**

### **Server Won't Start**
```powershell
# Check if migrations are applied
python manage.py showmigrations

# If not, run migrations
python manage.py migrate

# Check for errors
python manage.py check

# Try different port
python manage.py runserver 8080
```

### **Admin Shows Wrong Fields**
```
✅ FIXED: All 33 admin classes have been corrected
If you see errors, ensure you're using the latest code
```

### **Templates Not Loading**
```powershell
# Check template directories in settings.py
# Ensure 'templates' folder exists at project root
# Verify DIRS setting:
# 'DIRS': [BASE_DIR.parent / 'templates']
```

### **Static Files Not Found (CSS/JS)**
```powershell
# Collect static files
python manage.py collectstatic

# Check STATIC_URL and STATIC_ROOT in settings.py
```

### **Database Locked Error**
```
This happens with SQLite under heavy load
Solution: Restart server or switch to PostgreSQL for production
```

### **NoReverseMatch Error**
```
✅ FIXED: All URL patterns corrected in base.html
If you see this, check:
1. Model is registered in admin.py
2. URL name matches the admin registration
3. App is in INSTALLED_APPS
```

---

## 📊 **Database Models Summary**

### **Administration Module** (9 models)
- User, Student, Staff, Parent, Guardian, Department, Designation, SchoolProfile, AcademicYear

### **Academics Module** (12 models)
- Subject, ClassRoom, Grade, Term, Assignment, ExamType, Exam, ExamResult, Timetable, ClassSchedule, Curriculum, StudentPromotion

### **Finance Module** (7 models)
- FeeCategory, FeeStructure, Invoice, Payment, Expense, Budget, FinancialYear

### **Communication Module** (5 models)
- Announcement, Message, SMSLog, EmailLog, NotificationTemplate

### **Attendance Module** (5 models)
- StudentAttendance, StaffAttendance, AttendanceSummary, DisciplineIncident, BehaviorLog

### **LMS Module** (8 models)
- Course, Lesson, Resource, Quiz, Question, Answer, StudentProgress, Certificate

### **HR Module** (6 models)
- LeaveType, LeaveApplication, Payroll, Allowance, Deduction, PerformanceReview

### **Inventory Module** (5 models)
- Category, Item, Stock, StockMovement, Supplier

### **Transport Module** (5 models)
- Vehicle, Route, BusStop, StudentTransport, Driver

### **Security Module** (4 models)
- AuditLog, AccessLog, Permission, Role

### **Portals Module** (4 models)
- StudentPortal, TeacherPortal, ParentPortal, AdminPortal

### **Analytics Module** (4 models)
- PerformanceMetric, AttendanceReport, FinancialReport, CustomReport

### **Sync Module** (5 models) ✨ NEW!
- SyncLog, PendingSync, SyncConflict, DeviceRegistration, SyncSettings

**Total: 79+ models** across 13 modules

---

## 🤝 **Contributing**

### **Current Development Status**
This is an active development project. Currently focused on:
1. UI/UX modernization
2. Sync command implementation
3. Desktop app packaging

### **How to Contribute**
1. **Report Bugs**: Open an issue describing the problem
2. **Suggest Features**: Describe your feature idea
3. **Submit PRs**: Fork, create branch, make changes, submit PR
4. **Test Features**: Help test new functionality
5. **Documentation**: Improve docs, add tutorials

### **Development Guidelines**
- Follow Django best practices
- Write docstrings for new models/views
- Update README when adding features
- Test admin interface before committing
- Run `python manage.py check` before pushing

---

## 📞 **Support & Contact**

### **Issues & Questions**
- **GitHub Issues**: Report bugs or request features
- **Documentation**: See project documentation files

### **Known Issues**
1. ✅ **Admin field errors** - FIXED (all 93+ errors resolved)
2. ✅ **Attendance not registered** - FIXED (5 models added)
3. ✅ **URL routing errors** - FIXED (all navigation working)
4. 🔄 **Limited templates** - IN PROGRESS (8 created, 30+ needed)
5. ❌ **Sync not functional** - NOT STARTED (commands pending)
6. ❌ **Desktop app** - NOT STARTED (Phase 4)

---

## 📄 **License**

This project is currently under development for educational/commercial use.

---

## 🙏 **Acknowledgments**

- **Django Framework**: For the robust backend foundation
- **Bootstrap Team**: For the responsive UI framework
- **Font Awesome**: For beautiful icons
- **Chart.js**: For data visualization (planned)

---

## 📌 **Quick Reference**

### **Essential Commands**
```powershell
# Start server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Check for issues
python manage.py check

# Deployment check
python manage.py check --deploy
```

### **Important URLs**
- Dashboard: `http://127.0.0.1:8000/`
- Admin Panel: `http://127.0.0.1:8000/admin/`
- Login: `http://127.0.0.1:8000/accounts/login/`

### **Default Ports**
- Development: `8000`
- Alternative: `8080` (if 8000 is busy)

---

## 🔄 **Version History**

### **v0.9.0** (Current - January 2025)
- ✅ Fixed all 93+ admin field errors
- ✅ Created sync module with 5 models
- ✅ Registered attendance models (5 models)
- ✅ Fixed template navigation errors
- ✅ Server running with zero system check errors
- 🔄 Started UI modernization
- 🔄 Updated comprehensive README documentation

### **v0.8.0** (Previous)
- Initial Django project setup
- Created 12 modules with 74+ models
- Basic admin panel configuration
- Simple authentication system

---

**Last Updated**: January 2025  
**Status**: ✅ Backend Complete | 🔄 Frontend In Progress | ❌ Desktop Pending  
**Next Milestone**: Modern UI Implementation & Sync Commands

---

*Built with ❤️ using Django 6.0 & Python 3.13*
