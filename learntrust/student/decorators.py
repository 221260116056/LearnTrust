from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Course, Module


def role_required(role_name):
    """
    Decorator to check if user has required role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has studentprofile and correct role
            if not hasattr(request.user, 'studentprofile'):
                return HttpResponseForbidden("Profile not found")
            
            if request.user.studentprofile.role != role_name:
                return HttpResponseForbidden("Insufficient permissions")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
