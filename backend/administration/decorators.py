"""
Role-based access control decorators for frontend views
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(*allowed_roles):
    """
    Decorator to restrict view access by user role.
    Usage: @role_required('manager', 'head_teacher')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('frontend:dashboard')
        return wrapped_view
    return decorator


def manager_required(view_func):
    """Restrict to manager or admin"""
    return role_required('manager', 'admin')(view_func)


def head_teacher_or_manager(view_func):
    """Restrict to head teacher or manager"""
    return role_required('manager', 'admin', 'head_teacher')(view_func)


def teacher_or_above(view_func):
    """Restrict to teachers and above"""
    return role_required('manager', 'admin', 'head_teacher', 'teacher')(view_func)


def staff_only(view_func):
    """Restrict to all staff (no parents/students)"""
    return role_required('manager', 'admin', 'head_teacher', 'teacher', 'auxiliary')(view_func)


def auxiliary_required(view_func):
    """Restrict to auxiliary staff only"""
    return role_required('auxiliary')(view_func)


def bursar_or_manager(view_func):
    """Restrict to finance leaders (manager, admin, head teacher)"""
    return role_required('manager', 'admin', 'head_teacher')(view_func)


def parent_access(view_func):
    """Allow parents to access"""
    return role_required('parent')(view_func)


def student_access(view_func):
    """Allow students to access"""
    return role_required('student')(view_func)
