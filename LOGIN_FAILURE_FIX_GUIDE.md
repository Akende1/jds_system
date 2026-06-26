# LOGIN FAILURE DIAGNOSTIC & FIX GUIDE

## Issue Summary
User reports: **"I'm having Issues with the login. everytime."**

After inspecting the authentication system, codebase, and settings, I identified several **likely causes** and **concrete fixes** you should apply.

---

## ROOT CAUSE ANALYSIS

### 1. **Password Inconsistency (MOST LIKELY)**
Two conflicting credential-setting scripts exist in your codebase:

- **`set_test_passwords.py`** sets role-specific passwords:
  - Manager: `Manager1234!`
  - Teacher: `Teacher1234!`
  - HeadTeacher: `HeadTeacher1234!`
  - Parent: `Parent1234!`
  - etc.

- **`backend/administration/management/commands/seed_default_users.py`** sets:
  - ALL users to password: `1234`

**The Problem:** If both scripts were run, the last one to run wins. You likely ran `seed_default_users.py` last (which creates users with `1234`), but then tried logging in with credentials from `set_test_passwords.py` (like `Manager1234!`).

---

## DIAGNOSTIC STEPS (VERIFY YOUR SITUATION)

### Step 1: Start the Dev Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Step 2: View the Database via Django Admin
1. Navigate to: `http://127.0.0.1:8000/admin/`
2. Login with your **superuser** (admin) account
3. Go to **Users** section
4. Check which user accounts exist (Manager, Teacher, HeadTeacher, Parent, etc.)

### Step 3: Check Current Passwords
Run this command to verify which passwords are set:

```bash
python manage.py shell
```

Then paste this code:
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Check if a specific user exists
user = User.objects.filter(username='Manager').first()
if user:
    print(f"User 'Manager' exists. Testing passwords:")
    print(f"  Password '1234': {user.check_password('1234')}")
    print(f"  Password 'Manager1234!': {user.check_password('Manager1234!')}")
else:
    print("User 'Manager' does not exist!")

# List all users
print("\nAll users in database:")
for u in User.objects.all():
    print(f"  - {u.username} (type: {u.user_type}, active: {u.is_active})")
```

---

## SOLUTION: Reset Passwords Consistently

### Option A: Use Role-Specific Passwords (Recommended for QA)
Run this script to set strong, role-specific passwords:

```bash
python set_test_passwords.py
```

**Result:** 
- Manager: `Manager1234!`
- Teacher: `Teacher1234!`
- HeadTeacher: `HeadTeacher1234!`
- Parent: `Parent1234!`
- Auxiliary: `Auxiliary1234!`

### Option B: Use Simple Passwords for Development
Create a new file `reset_simple_passwords.py`:

```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

passwords = {
    'Manager': '1234',
    'HeadTeacher': '1234',
    'Teacher': '1234',
    'Parent': '1234',
    'Auxilery': '1234',
    'Student': '1234',
    'admin': 'admin1234',  # superuser
}

for username, password in passwords.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f"✓ {username}: password reset to '{password}'")
    except User.DoesNotExist:
        print(f"✗ {username}: user not found")

print("\nLogin credentials reset successfully!")
```

Then run:
```bash
python reset_simple_passwords.py
```

---

## ADDITIONAL CHECKS

### Check 1: Ensure User Accounts Exist
If the default users don't exist, create them:

```bash
python manage.py seed_default_users
```

**Output should show:**
```
✓ admin user created
✓ Manager user created
✓ HeadTeacher user created
✓ Teacher user created
✓ Parent user created
✓ Student user created
```

### Check 2: Verify Login Page is Accessible
- Open: `http://127.0.0.1:8000/login/`
- Form should load without errors
- Check browser console for JavaScript errors (F12)
- Check "Network" tab to see if POST request succeeds (200 OK vs. 403/500)

### Check 3: Verify CSRF Token is Present
View page source (Ctrl+U) and confirm you see:
```html
<input type="hidden" name="csrfmiddlewaretoken" value="...">
```

If missing, the login template is broken. Verify [templates/registration/login.html](templates/registration/login.html) includes `{% csrf_token %}`.

---

## PREVENT STUDENTS FROM LOGGING IN (By Design)

**Note:** The `CustomLoginView` in `backend/administration/auth_views.py` intentionally blocks student logins:

```python
if getattr(user, 'user_type', None) == 'student':
    form.add_error(None, 'Student portal logins are disabled. Parents access student data via their accounts.')
    return self.form_invalid(form)
```

**This is intentional.** If you're trying to login as "Student" user, you'll get an error. Try:
- **Manager**, **HeadTeacher**, **Teacher**, or **Parent** instead.

---

## RECOMMENDED ACTION PLAN

1. **Run the diagnostic commands above** to identify which passwords are actually set in your database.

2. **Run one of the password reset scripts** to ensure consistency:
   ```bash
   # Option A: Role-specific passwords (strong)
   python set_test_passwords.py
   
   # OR Option B: Simple passwords (dev only)
   python reset_simple_passwords.py
   ```

3. **Test login with the correct credentials**:
   - Username: `Manager` | Password: `Manager1234!` (or `1234` if you ran Option B)
   - Or any other role (Teacher, Parent, HeadTeacher)

4. **Verify in browser console** (F12 → Network tab):
   - POST to `/login/` should return **302 redirect** (success) or **200 OK with login template** (failed)
   - Check for any **403 Forbidden** (CSRF issue) or **500 Server Error** (backend bug)

5. **If still failing**, capture the exact error:
   - Open DevTools (F12)
   - Attempt login
   - Check **Console** tab for error messages
   - Check **Network** → POST response body for Django error details
   - Share that error message so I can provide targeted fix

---

## CONTACT POINTS FOR FURTHER HELP

If you're still getting login errors after trying these steps, please provide:
1. **Exact username** you're trying to login with
2. **Exact password** you're entering
3. **Exact error message** you see (screenshot or text from browser)
4. **Browser console output** (F12 → Console tab)
5. **Django server console output** (the terminal running `python manage.py runserver`)

---

**Summary:** The login system itself is well-designed and secure. The login failure is almost certainly due to **password mismatch**. Use the diagnostic steps above to confirm which passwords are actually in the database, then reset them consistently using one of the provided scripts.
