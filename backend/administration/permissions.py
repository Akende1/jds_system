"""
User Hierarchy and Permission System
Implements hierarchical user permissions with cascading access control
"""

from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

# Extend User model with hierarchy field
# This should be added to the User model in models.py:
# reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')


class UserHierarchy:
    """Helper class to manage user hierarchy and permissions"""
    
    # Define hierarchy levels (lower number = higher authority)
    HIERARCHY_LEVELS = {
        'admin': 1,
        'manager': 2,
        'head_teacher': 3,
        'teacher': 4,
        'auxiliary': 5,
        'parent': 6,
        'student': 7,
    }
    
    # Permission matrix: {user_type: {resource: [allowed_actions]}}
    PERMISSION_MATRIX = {
        'admin': {
            # Full access to everything
            'students': ['view', 'add', 'edit', 'delete', 'import', 'export'],
            'staff': ['view', 'add', 'edit', 'delete', 'export'],
            'classes': ['view', 'add', 'edit', 'delete', 'assign'],
            'fees': ['view', 'add', 'edit', 'delete', 'collect', 'refund', 'export'],
            'attendance': ['view', 'add', 'edit', 'delete', 'export'],
            'grades': ['view', 'add', 'edit', 'delete', 'export'],
            'reports': ['view', 'generate', 'schedule', 'send'],
            'settings': ['view', 'edit'],
            'users': ['view', 'add', 'edit', 'delete', 'assign_roles'],
            'promotions': ['view', 'approve', 'reject'],
            'transfers': ['view', 'approve', 'reject', 'execute'],
            'assessments': ['view', 'add', 'edit', 'delete'], # Admin can manage all assessments
            'report_cards': ['view', 'generate', 'approve', 'edit', 'delete'], # Admin can manage all report cards
            'timetable': ['view', 'add', 'edit', 'delete', 'approve'],
        },
        'manager': {
            # Manager: Can manage most things except critical settings
            'students': ['view', 'add', 'edit', 'import', 'export'],
            'staff': ['view', 'export'],
            'classes': ['view', 'add', 'edit', 'assign'],
            'fees': ['view', 'add', 'edit', 'collect', 'export'],
            'attendance': ['view', 'add', 'edit', 'export'],
            'grades': ['view', 'add', 'edit', 'export'],
            'reports': ['view', 'generate', 'send'],
            'settings': ['view'],
            'users': ['view'],
            'promotions': ['view', 'approve'],
            'transfers': ['view', 'approve', 'execute'],
            'assessments': ['view', 'add', 'edit'], # Manager can oversee assessments
            'report_cards': ['view', 'generate', 'approve', 'edit'], # Manager can approve/edit report cards
            'timetable': ['view', 'add', 'edit', 'approve'],
        },
        'head_teacher': {
            # Head Teacher: Can manage teachers and students, approve academic matters
            'students': ['view', 'add', 'edit', 'export'],
            'staff': ['view'],
            'classes': ['view', 'assign'],
            'fees': ['view', 'export'],
            'attendance': ['view', 'add', 'edit', 'export'],
            'grades': ['view', 'add', 'edit', 'export'],
            'reports': ['view', 'generate'],
            'settings': ['view'],
            'users': ['view'],
            'promotions': ['view', 'approve'],
            'transfers': ['view'],
            'assessments': ['view', 'add', 'edit'], # Head Teacher can oversee assessments
            'report_cards': ['view', 'generate', 'approve', 'edit'], # Head Teacher can approve/edit report cards
            'timetable': ['view', 'add', 'edit', 'approve'],
        },
        'teacher': {
            # Teacher: Can only manage own classes
            'students': ['view', 'export'],  # Only students in their classes
            'staff': [],
            'classes': ['view'],  # Only assigned classes
            'fees': ['view'],  # Only for their students
            'attendance': ['view', 'add', 'edit'],  # Only for their classes
            'grades': ['view', 'add', 'edit'],  # Only for their students
            'reports': ['view', 'generate'],  # Only for their classes
            'settings': [],
            'users': [],
            'promotions': ['view'],
            'transfers': [],
            'assessments': ['view', 'add', 'edit'], # Teachers can add/edit their own assessments
            'report_cards': ['view', 'generate', 'edit'], # Teachers can generate and edit their students' report cards
            'timetable': ['view', 'add', 'edit'],
        },
        'auxiliary': {
            # Support Staff: Limited read access
            'students': ['view'],
            'staff': [],
            'classes': ['view'],
            'fees': ['view'],
            'attendance': ['view'],
            'grades': ['view'],
            'reports': ['view'],
            'settings': [],
            'users': [],
            'promotions': [],
            'transfers': [],
            'assessments': ['view'],
            'report_cards': ['view'],
            'timetable': ['view'],
        },
        'parent': {
            # Parent: Can only view own children's data
            'students': ['view'],  # Only own children
            'staff': [],
            'classes': ['view'],  # Child's classes
            'fees': ['view'],  # Own payments
            'attendance': ['view'],  # Child's attendance
            'grades': ['view'],  # Child's grades
            'reports': ['view'],  # Child's reports
            'settings': [],
            'users': [],
            'promotions': [],
            'transfers': [],
            'assessments': ['view'], # Parents can view their children's assessment results
            'report_cards': ['view'], # Parents can view their children's report cards
            'timetable': ['view'],
        },
        'student': {
            # Student: Can only view own data
            'students': ['view'],  # Only self
            'staff': [],
            'classes': ['view'],  # Own classes
            'fees': ['view'],  # Own fees
            'attendance': ['view'],  # Own attendance
            'grades': ['view'],  # Own grades
            'reports': ['view'],  # Own reports
            'settings': [],
            'users': [],
            'promotions': [],
            'transfers': [],
            'assessments': ['view'], # Students can view their own assessment results
            'report_cards': ['view'], # Students can view their own report cards
            'timetable': ['view'],
        },
    }
    
    @classmethod
    def get_hierarchy_level(cls, user):
        """Get numeric hierarchy level for a user"""
        return cls.HIERARCHY_LEVELS.get(user.user_type, 999)
    
    @classmethod
    def can_access(cls, user, resource, action):
        """Check if user can perform action on resource"""
        if not user or not user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if user.is_superuser:
            return True
        
        # Get user's permissions for this resource
        user_permissions = cls.PERMISSION_MATRIX.get(user.user_type, {})
        allowed_actions = user_permissions.get(resource, [])
        
        return action in allowed_actions
    
    @classmethod
    def has_higher_authority(cls, user, target_user):
        """Check if user has higher authority than target_user"""
        if user.is_superuser:
            return True
        
        user_level = cls.get_hierarchy_level(user)
        target_level = cls.get_hierarchy_level(target_user)
        
        return user_level < target_level
    
    @classmethod
    def can_manage_user(cls, user, target_user):
        """Check if user can manage (edit/delete) target_user"""
        if not cls.has_higher_authority(user, target_user):
            return False
        
        # Check if target reports to user (direct or indirect)
        if hasattr(target_user, 'reports_to'):
            current = target_user.reports_to
            while current:
                if current == user:
                    return True
                current = getattr(current, 'reports_to', None)
        
        # If user has higher authority, allow management
        return True
    
    @classmethod
    def get_subordinates(cls, user, include_indirect=True):
        """Get all users under this user in hierarchy"""
        if not hasattr(user, 'subordinates'):
            return User.objects.none()
        
        subordinates = set(user.subordinates.all())
        
        if include_indirect:
            # Recursively get all subordinates
            for subordinate in list(subordinates):
                subordinates.update(cls.get_subordinates(subordinate, include_indirect=True))
        
        return User.objects.filter(id__in=[s.id for s in subordinates])
    
    @classmethod
    def get_accessible_students(cls, user):
        """Get students accessible to this user"""
        from administration.models import Student
        
        if user.user_type == 'admin' or user.user_type == 'manager':
            # Full access
            return Student.objects.all()
        
        elif user.user_type == 'head_teacher':
            # All students
            return Student.objects.all()
        
        elif user.user_type == 'teacher':
            # Students in classes taught by this teacher
            return Student.objects.filter(
                Q(current_class__teacher_assignments__teacher=user, current_class__teacher_assignments__is_active=True) |
                Q(current_class__class_teacher=user)
            ).distinct()
        
        elif user.user_type == 'parent':
            # Own children (assuming guardian relationship exists)
            return Student.objects.filter(
                guardian_email=user.email
            ) | Student.objects.filter(
                guardian_phone=user.phone_number
            )
        
        elif user.user_type == 'student':
            # Only self
            return Student.objects.filter(user=user)
        
        else:
            return Student.objects.none()
    
    @classmethod
    def get_accessible_classes(cls, user):
        """Get classes accessible to this user"""
        from administration.models import ClassRoom
        from administration.models import Student as StudentModel
        
        if user.user_type in ['admin', 'manager', 'head_teacher']:
            return ClassRoom.objects.all()
        
        elif user.user_type == 'teacher':
            # Classes taught by this teacher
            return ClassRoom.objects.filter(
                teacher_assignments__teacher=user,
                teacher_assignments__is_active=True
            ).distinct()
        
        elif user.user_type == 'parent':
            # Classes of own children
            students = cls.get_accessible_students(user)
            return ClassRoom.objects.filter(
                students__in=students
            ).distinct()
        
        elif user.user_type == 'student':
            # Own class
            try:
                student = StudentModel.objects.select_related('current_class').get(user=user)
                if student.current_class:
                    return ClassRoom.objects.filter(id=getattr(student.current_class, 'pk', None))
            except StudentModel.DoesNotExist:
                pass
        
        return ClassRoom.objects.none()


class PermissionChecker:
    """Decorator and utility class for permission checking"""
    
    def __init__(self, resource, action):
        self.resource = resource
        self.action = action
    
    def __call__(self, func):
        """Decorator to check permissions before executing function"""
        def wrapper(request, *args, **kwargs):
            if not UserHierarchy.can_access(request.user, self.resource, self.action):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(f'You do not have permission to {self.action} {self.resource}')
            return func(request, *args, **kwargs)
        return wrapper
    
    @staticmethod
    def check_permission(user, resource, action):
        """Static method for permission checking"""
        return UserHierarchy.can_access(user, resource, action)


# Convenience functions for common permission checks
def can_view_students(user):
    return UserHierarchy.can_access(user, 'students', 'view')

def can_edit_students(user):
    return UserHierarchy.can_access(user, 'students', 'edit')

def can_approve_promotions(user):
    return UserHierarchy.can_access(user, 'promotions', 'approve')

def can_collect_fees(user):
    return UserHierarchy.can_access(user, 'fees', 'collect')

def can_manage_users(user):
    return UserHierarchy.can_access(user, 'users', 'edit')
