from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.crypto import get_random_string
import secrets

# Custom User Model
class User(AbstractUser):
    """Extended User model to support different user types in the school system"""
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('head_teacher', 'Head Teacher'),
        ('teacher', 'Teacher'),
        ('auxiliary', 'Auxiliary Staff'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=17, blank=True)
    is_active_user = models.BooleanField(default=True)
    onboarding_completed = models.BooleanField(default=False)
    onboarding_token = models.CharField(max_length=128, null=True, blank=True, unique=True)
    onboarding_token_created_at = models.DateTimeField(null=True, blank=True)
    
    # Hierarchical reporting structure
    reports_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subordinates',
        help_text='Direct supervisor/manager in organizational hierarchy'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"


class PasswordResetToken(models.Model):
    """Model to store password reset tokens with expiration"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
    
    def __str__(self):
        return f"Reset Token for {self.user.username}"
    
    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def create_token(user, expires_in_hours=24):
        """Create a new password reset token for a user"""
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)
        
        # Delete any existing token for this user
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Create new token
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        return reset_token


class AcademicYear(models.Model):
    """Represents an academic year (e.g., 2024/2025)"""
    name = models.CharField(max_length=50, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other academic years to not current
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(models.Model):
    """Represents a school term within an academic year"""
    TERM_CHOICES = (
        ('1', 'First Term'),
        ('2', 'Second Term'),
        ('3', 'Third Term'),
    )
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    term_number = models.CharField(max_length=1, choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['academic_year', 'term_number']
        unique_together = ['academic_year', 'term_number']
        
    def __str__(self):
        return f"{self.academic_year.name} - {self.get_term_number_display()}"
        
    def save(self, *args, **kwargs):
        if self.is_current:
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Grade(models.Model):
    """Represents grade levels (e.g., Grade 1, Grade 2, etc.)"""
    name = models.CharField(max_length=50, unique=True)  # e.g., "Grade 1", "Grade 2"
    level = models.IntegerField()  # Numeric representation for ordering
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level']
        
    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    """Represents a specific class (e.g., Grade 1A, Grade 2B)"""
    CLASS_SECTION_CHOICES = (
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
        ('D', 'Section D'),
        ('E', 'Section E'),
    )
    
    name = models.CharField(max_length=100, blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classrooms')
    section = models.CharField(max_length=1, choices=CLASS_SECTION_CHOICES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classrooms')
    class_teacher = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, 
                                      limit_choices_to={'user_type': 'teacher'}, 
                                      related_name='class_teacher_of')
    room_number = models.CharField(max_length=20, blank=True)
    capacity = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['grade__level', 'section']
        unique_together = ['grade', 'section', 'academic_year']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        
    def __str__(self):
        return self.name or f"{self.grade.name}{self.section} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        self.name = f"{self.grade.name}{self.section}"
        super().save(*args, **kwargs)
        
    @property
    def student_count(self):
        return self.students.count()


class Student(models.Model):
    """Student profile with complete information"""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=20, unique=True)
    admission_date = models.DateField()
    current_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    
    # Personal Information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='Nigerian')
    religion = models.CharField(max_length=50, blank=True)
    
    # Parent/Guardian Information
    parent = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True,
                               limit_choices_to={'user_type': 'parent'}, 
                               related_name='children')
    guardian_name = models.CharField(max_length=200)
    guardian_relationship = models.CharField(max_length=50)
    guardian_phone = models.CharField(max_length=17)
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField()
    
    # Medical Information
    medical_conditions = models.TextField(blank=True, help_text="Any known allergies or medical conditions")
    
    # Status
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, 
                             choices=(('active', 'Active'), 
                                    ('suspended', 'Suspended'), 
                                    ('graduated', 'Graduated'), 
                                    ('withdrawn', 'Withdrawn')),
                             default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['admission_number']
        
    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name()}"
        
    @property
    def full_name(self):
        return self.user.get_full_name()


class EditRequest(models.Model):
    """A request initiated by a parent to edit a student's record, reviewed by staff."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    parent = models.ForeignKey('User', on_delete=models.CASCADE, related_name='edit_requests', limit_choices_to={'user_type': 'parent'})
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='edit_requests')
    field_name = models.CharField(max_length=100)
    requested_value = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_edit_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"EditRequest({self.student} - {self.field_name}) [{self.status}]"


class Staff(models.Model):
    """Staff/Employee profiles for all staff types"""
    STAFF_TYPE_CHOICES = (
        ('manager', 'Manager'),
        ('head_teacher', 'Head Teacher'),
        ('teacher', 'Teacher'),
        ('auxiliary', 'Auxiliary Staff'),
    )
    
    EMPLOYMENT_TYPE_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    )
    
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='staff_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    
    # Employment Details
    date_of_joining = models.DateField()
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    
    # Contact & Personal
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female'), ('O', 'Other')))
    marital_status = models.CharField(max_length=20, 
                                     choices=(('single', 'Single'), 
                                            ('married', 'Married'), 
                                            ('divorced', 'Divorced'), 
                                            ('widowed', 'Widowed')),
                                     blank=True)
    
    # Banking Details
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=20, blank=True)

    # Onboarding documentation
    tpin_no = models.CharField(max_length=50, blank=True)
    nrc_no = models.CharField(max_length=50, blank=True)
    nrc_front = models.FileField(upload_to='staff_documents/nrc/', null=True, blank=True)
    nrc_back = models.FileField(upload_to='staff_documents/nrc/', null=True, blank=True)
    other_documents = models.FileField(upload_to='staff_documents/other/', null=True, blank=True)
    digital_signature = models.ImageField(upload_to='signatures/staff/', null=True, blank=True)
    profile_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['staff_id']
        verbose_name_plural = 'Staff'
        
    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()} ({self.get_staff_type_display()})"


class StaffRole(models.Model):
    """
    Many-to-many style model to assign specialized roles to auxiliary staff.
    Allows one staff member to have multiple roles (e.g., cleaning + cooking).
    """
    ROLE_CHOICES = (
        ('cleaning', 'Cleaning Staff'),
        ('cooking', 'Cooking Staff'),
        ('cleaning_cooking', 'Cleaning & Cooking Staff'),
        ('security', 'Security Staff'),
    )
    
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='roles')
    role_type = models.CharField(max_length=30, choices=ROLE_CHOICES)
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'role_type']
        ordering = ['-is_active', '-assigned_date']
        
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_role_type_display()}"


class SchoolInformation(models.Model):
    """Singleton model to store school information"""
    school_name = models.CharField(max_length=200)
    school_code = models.CharField(max_length=20, unique=True)
    motto = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='school/', null=True, blank=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=17)
    website = models.URLField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Nigeria')
    
    # Principal/Head
    principal_name = models.CharField(max_length=200)
    principal_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'School Information'
        verbose_name_plural = 'School Information'
        
    def __str__(self):
        return self.school_name
        
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SchoolInformation.objects.exists():
            raise ValueError('Only one School Information instance is allowed')
        super().save(*args, **kwargs)


class Notification(models.Model):
    """
    Notification system for admin/manager approvals.
    Tracks pending requests from all sources (restocking, student edits, teacher requests, etc.)
    """
    NOTIFICATION_TYPES = (
        ('restocking_request', 'Restocking Request'),
        ('edit_request', 'Student Edit Request'),
        ('teacher_request', 'Teacher Request'),
        ('expense_request', 'Expense Request'),
        ('approval_request', 'Approval Request'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    )
    
    # Recipients
    recipient = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    
    # Link to related object
    content_type = models.CharField(max_length=100, blank=True, help_text="e.g., 'RestockingRequest', 'EditRequest'")
    object_id = models.IntegerField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['recipient', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'unread':
            from django.utils import timezone
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


class ApprovalRequest(models.Model):
    REQUEST_TYPES = (
        ('restock', 'Restock Request'),
        ('student_edit', 'Student Edit Request'),
        ('expense', 'Expense Approval'),
        ('payroll', 'Payroll Approval'),
        ('event', 'Academic Event Approval'),
        ('communication', 'Communication Approval'),
    )

    STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    requested_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='requests_made')
    assigned_to = models.ManyToManyField('User', related_name='requests_to_review', blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_approval_requests')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_type', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.status}"

    @property
    def content_object(self):
        model_class = self.content_type.model_class()
        return model_class.objects.get(pk=self.object_id)

