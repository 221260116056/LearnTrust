from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Enrollment, StudentProgress, Module


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
