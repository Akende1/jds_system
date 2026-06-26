# 🚀 Quick Start Guide - School Management System

## ⚡ Fast Setup (5 Minutes)

### 1. Verify Installation
Your project is already set up! Just verify everything is working:

```powershell
cd C:\Users\rival\Documents\jds_system
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py check
```

### 2. Create Admin User
```powershell
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py createsuperuser
```

Enter:
- Username: `admin`
- Email: `admin@school.com`
- Password: (your secure password)
- Password (again): (confirm)

### 3. Load Sample Data (Optional but Recommended)
```powershell
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py setup_demo_data
```

This creates:
- School information
- Academic year 2025/2026
- 3 Terms
- Grades 1-6 with sections A & B
- Core subjects (Math, English, Science, etc.)
- Sample teacher (username: `teacher`, password: `teacher123`)
- Sample student (username: `student`, password: `student123`)

### 4. Start the Server
```powershell
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py runserver
```

### 5. Access the System
Open your browser and go to:
- **Main Dashboard**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- Login with your superuser credentials

## 🎨 Frontend Features

The system now includes a **fully functional web interface** with:

### ✅ Available Pages

1. **Dashboard** (`/`)
   - Overview statistics (students, staff, fees)
   - Attendance summary
   - Recent registrations
   - Quick actions

2. **Students** (`/students/`)
   - List all students with filters
   - Search by name or admission number
   - Filter by class
   - View detailed student profiles

3. **Student Details** (`/students/<id>/`)
   - Personal information
   - Guardian details
   - Attendance percentage
   - Recent exam results
   - Fee payment status

4. **Staff** (`/staff/`)
   - List all staff members
   - Filter by type (teaching/non-teaching)
   - Search by name or employee ID

5. **Staff Details** (`/staff/<id>/`)
   - Employment information
   - Attendance records

6. **Finance** (`/finance/invoices/`)
   - Fee invoices list
   - Payment records
   - Expense tracking

7. **Academics** (`/academics/`)
   - Subjects
   - Exams
   - Results

8. **Attendance** (`/attendance/`)
   - Student attendance
   - Staff attendance
   - Attendance marking

### 🎯 Quick Login Options

After running `setup_demo_data`, you can login as:

1. **Admin** (Full Access)
   - Username: `admin`
   - Password: (what you set during createsuperuser)

2. **Teacher** (Staff Member)
   - Username: `teacher`
   - Password: `teacher123`

3. **Student** (Student Portal)
   - Username: `student`
   - Password: `student123`

## 📝 First Steps After Login

### Step 1: Configure School Information
1. Go to **Administration** → **School Information**
2. Click **Add School Information**
3. Fill in your school details:
   - School Name
   - School Code
   - Motto
   - Contact Information
   - Principal Details
4. Save

### Step 2: Create Academic Year
1. Go to **Administration** → **Academic Years**
2. Click **Add Academic Year**
3. Example:
   - Name: `2024/2025`
   - Start Date: `2024-09-01`
   - End Date: `2025-06-30`
   - Is Current: ✓ (check this)
4. Save

### Step 3: Create Terms
1. Go to **Administration** → **Terms**
2. Create three terms:

**First Term:**
- Academic Year: `2024/2025`
- Term Number: `First Term`
- Start Date: `2024-09-01`
- End Date: `2024-12-15`
- Is Current: ✓

**Second Term:**
- Academic Year: `2024/2025`
- Term Number: `Second Term`
- Start Date: `2025-01-06`
- End Date: `2025-03-30`

**Third Term:**
- Academic Year: `2024/2025`
- Term Number: `Third Term`
- Start Date: `2025-04-20`
- End Date: `2025-06-30`

### Step 4: Create Grades
1. Go to **Administration** → **Grades**
2. Add grades (examples):
   - Name: `Grade 1`, Level: `1`
   - Name: `Grade 2`, Level: `2`
   - Name: `Grade 3`, Level: `3`
   - Continue up to your highest grade...

### Step 5: Create Classes
1. Go to **Administration** → **Classes**
2. Example:
   - Grade: `Grade 1`
   - Section: `A`
   - Academic Year: `2024/2025`
   - Room Number: `101`
   - Capacity: `30`
3. Create multiple classes (1A, 1B, 2A, 2B, etc.)

### Step 6: Create Subjects
1. Go to **Academics** → **Subjects**
2. Examples:
   - Name: `Mathematics`, Code: `MATH`
   - Name: `English`, Code: `ENG`
   - Name: `Science`, Code: `SCI`
   - Name: `Social Studies`, Code: `SST`

### Step 7: Add First Teacher
1. Go to **Administration** → **Users**
2. Click **Add User**
3. Fill in:
   - Username: `teacher1`
   - Password: (set password)
   - First name: `John`
   - Last name: `Doe`
   - Email: `john.doe@school.com`
   - User type: `Teacher`
   - Phone number: `+2348012345678`
4. Save

5. Now go to **Administration** → **Staff**
6. Click **Add Staff**
7. Link to the user you just created
8. Fill in employment details
9. Save

### Step 8: Add First Student
1. Go to **Administration** → **Users**
2. Create a user with `user_type = Student`

3. Go to **Administration** → **Students**
4. Click **Add Student**
5. Fill in:
   - User: (select the student user)
   - Admission Number: `STU001`
   - Admission Date: (today)
   - Current Class: `Grade 1A`
   - Gender: `M` or `F`
   - Guardian details (required)
6. Save

### Step 9: Set Up Fee Structure
1. Go to **Finance** → **Fee Structures**
2. Example:
   - Name: `Tuition Fee - Grade 1`
   - Fee Type: `Tuition Fee`
   - Grade: `Grade 1`
   - Academic Year: `2024/2025`
   - Amount: `50000`
   - Payment Frequency: `Per Term`
3. Create fee structures for each grade

### Step 10: Mark Attendance
1. Go to **Attendance** → **Student Attendances**
2. Click **Add Student Attendance**
3. Select student, date, and status
4. Save

## 🎯 Common Tasks

### Recording a Payment
1. **Finance** → **Payments** → **Add Payment**
2. Fill in invoice, student, amount, and payment method
3. Save - the invoice balance updates automatically

### Creating an Exam
1. **Academics** → **Exams** → **Add Exam**
2. Select subject, class, and date
3. Set max marks and pass marks
4. Save

### Recording Exam Results
1. **Academics** → **Exam Results** → **Add Exam Result**
2. Select exam and student
3. Enter marks obtained
4. Grade is calculated automatically

### Posting an Announcement
1. **Communication** → **Announcements** → **Add Announcement**
2. Write title and content
3. Select target audience
4. Set priority
5. Save

### Assigning Transport
1. **Transport** → **Routes** → Create routes first
2. **Transport** → **Transport Assignments** → Assign students

## 📊 Viewing Reports

### Performance Reports
- **Analytics** → **Performance Trends**

### Financial Reports
- **Finance** → **Financial Reports**

### Attendance Reports
- **Attendance** → **Attendance Summaries**

## 🔧 Troubleshooting

### Server Won't Start
```powershell
# Check for errors
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py check

# Try a different port
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py runserver 8080
```

### Static Files Not Loading
```powershell
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py collectstatic
```

### Database Issues
```powershell
# Reset database (WARNING: Deletes all data!)
cd C:\Users\rival\Documents\jds_system\backend
del db.sqlite3
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py migrate
C:\Users\rival\Documents\jds_system\venv\Scripts\python.exe manage.py createsuperuser
```

## 💡 Tips

1. **Always create users first** before creating Students or Staff profiles
2. **Set one Academic Year as current** - only one can be current at a time
3. **Use the search feature** in admin lists to find records quickly
4. **Export data** using the admin actions (top-right of list pages)
5. **Take regular backups** of your database

## 🎓 Next Level

Once you're comfortable with basic operations:
- Explore the **LMS module** for e-learning
- Set up **Transport routes** if needed
- Configure **Payroll** for staff salary management
- Use **Analytics** to track school performance
- Customize **User Roles** for fine-grained permissions

## 📞 Need Help?

- Check the full **README.md** for detailed documentation
- Review Django admin documentation: https://docs.djangoproject.com/
- Each model has help text in the admin interface

---

**🎉 You're all set! Start managing your school efficiently!**
