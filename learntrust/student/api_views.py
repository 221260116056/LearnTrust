import hashlib
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Enrollment, StudentProgress, Module, WatchEvent


# =====================================================
# API — WATCH EVENT
# =====================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def watch_event_api(request):
    """
    Secure watch event logging
    """
    module_id = request.data.get("module_id")
    event_type = request.data.get("event_type")
    sequence_number = request.data.get("sequence_number")

    if not all([module_id, event_type, sequence_number]):
        return Response({"status": "error", "message": "Missing required fields"}, status=400)

    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({"status": "error", "message": "Module not found"}, status=404)

    if WatchEvent.objects.filter(student=request.user, module=module, sequence_number=sequence_number).exists():
        return Response({"status": "error", "message": "Duplicate sequence_number"}, status=409)

    hash_input = f"{request.user.id}{module_id}{sequence_number}{settings.SECRET_KEY}"
    token_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    WatchEvent.objects.create(
        student=request.user,
        module=module,
        event_type=event_type,
        sequence_number=sequence_number,
        token_hash=token_hash,
        current_time=0.0
    )

    return Response({"status": "success", "message": "Event recorded"})


# =====================================================
# API — ENROLLMENTS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def enrollment_api(request):
    """
    Return all enrollments for logged-in student
    """

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related("course")

    data = [
        {
            "course_id": e.course.id,
            "course": e.course.title,
            "paid": e.is_paid
        }
        for e in enrollments
    ]

    return Response({
        "status": "success",
        "count": len(data),
        "enrollments": data
    })


# =====================================================
# API — MY COURSES
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_courses_api(request):
    """
    Return paid courses
    """

    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_paid=True
    ).select_related("course")

    courses = [
        {
            "course_id": e.course.id,
            "title": e.course.title,
            "status": "enrolled"
        }
        for e in enrollments
    ]

    return Response({
        "status": "success",
        "count": len(courses),
        "courses": courses
    })


# =====================================================
# API — DASHBOARD SUMMARY
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """
    Dashboard overview
    """

    paid_courses = Enrollment.objects.filter(
        student=request.user,
        is_paid=True
    )

    completed_modules = StudentProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).count()

    return Response({
        "status": "success",
        "welcome": f"Welcome {request.user.username}",
        "total_courses": paid_courses.count(),
        "completed_modules": completed_modules
    })


# =====================================================
# API — PROGRESS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def progress_api(request):
    """
    Completion percentage
    """

    total_modules = Module.objects.count()

    completed = StudentProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).count()

    percent = int((completed / total_modules) * 100) if total_modules else 0

    return Response({
        "status": "success",
        "total_modules": total_modules,
        "completed_modules": completed,
        "progress_percent": percent
    })
