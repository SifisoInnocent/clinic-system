from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def role_required(*allowed_roles):
    """
    Decorator to require specific user roles
    Usage: @role_required('student', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                messages.error(request, 'User role not defined')
                return redirect('accounts:login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page')
                return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def student_required(view_func):
    """Decorator to require student role"""
    return role_required('student')(view_func)


def staff_required(view_func):
    """Decorator to require staff role (nurse or psychologist)"""
    return role_required('nurse', 'psychologist')(view_func)


def admin_required(view_func):
    """Decorator to require admin role"""
    return role_required('admin')(view_func)


def admin_or_staff_required(view_func):
    """Decorator to require admin or staff role"""
    return role_required('admin', 'nurse', 'psychologist')(view_func)
