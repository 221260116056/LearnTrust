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
    Returns all enrollments for the logged-in student
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
    Returns paid enrolled courses for the logged-in student
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
    Dashboard stats for logged-in student
    """

    enrollments = Enrollment.objects.filter(
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
        "total_courses": enrollments.count(),
        "completed_modules": completed_modules
    })


# =====================================================
# API — STUDENT PROGRESS
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def progress_api(request):
    """
    Overall module completion progress for student
    """

    total_modules = Module.objects.count()

    completed = StudentProgress.objects.filter(
        student=request.user,
        is_completed=True
    ).count()

    percent = 0
    if total_modules > 0:
        percent = int((completed / total_modules) * 100)

    return Response({
        "status": "success",
        "total_modules": total_modules,
        "completed_modules": completed,
        "progress_percent": percent
    })
