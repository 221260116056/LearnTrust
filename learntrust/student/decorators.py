from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from .models import Course, Module, TeacherRegistrationRequest


def role_required(role_name):
    """
    Decorator to check if user has required role.
    For teachers, also checks if their registration request has been approved.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has studentprofile and correct role
            if not hasattr(request.user, 'studentprofile'):
                return HttpResponseForbidden("Profile not found")
            
            if request.user.studentprofile.role != role_name:
                return HttpResponseForbidden("Insufficient permissions")
            
            # For teachers, check if their registration request is approved
            if role_name == 'teacher':
                try:
                    teacher_request = TeacherRegistrationRequest.objects.get(user=request.user)
                    if teacher_request.status != 'approved':
                        # Redirect to pending approval page
                        from django.urls import reverse
                        return redirect('teacher_pending_approval')
                except TeacherRegistrationRequest.DoesNotExist:
                    # No request found - user might be an old teacher, allow access
                    # Or redirect to pending if they should have a request
                    pass
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
