from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone

from .models import (
    Course,
    Enrollment,
    Module,
    StudentProgress,
    StudentProfile,
    Notification
)

# ---------------------------------
# HELPER: COURSE PROGRESS %
# ---------------------------------
def course_progress(student, course):
    total = Module.objects.filter(course=course).count()
    completed = StudentProgress.objects.filter(
        student=student,
        course=course,
        is_completed=True
    ).count()

    if total == 0:
        return 0

    return int((completed / total) * 100)


# ---------------------------------
# LOGIN (EMAIL BASED)
# ---------------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")   # email entered in username field
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid email or password")

    return render(request, "student/login.html")


# ---------------------------------
# DASHBOARD
# ---------------------------------
@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_paid=True
    ).select_related("course")

    courses_progress = [
        {
            "course": enroll.course,
            "progress": course_progress(request.user, enroll.course)
        }
        for enroll in enrollments
    ]

    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by("-created_at")[:5]

    return render(request, "student/dashboard.html", {
        "courses_progress": courses_progress,
        "notifications": notifications
    })


# ---------------------------------
# MY COURSES
# ---------------------------------
@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_paid=True
    ).select_related("course")

    return render(request, "student/my_courses.html", {
        "enrollments": enrollments
    })


# ---------------------------------
# COURSE DETAIL
# ---------------------------------
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_paid=True
    ).first()

    modules_ui = []

    if enrollment:
        modules = Module.objects.filter(course=course).order_by("order")
        progress_qs = StudentProgress.objects.filter(student=request.user)

        previous_completed = True

        for module in modules:
            completed = progress_qs.filter(
                module=module,
                is_completed=True
            ).exists()

            modules_ui.append({
                "id": module.id,
                "title": module.title,
                "order": module.order,
                "unlocked": previous_completed,
                "completed": completed
            })

            previous_completed = completed

    return render(request, "student/course_detail.html", {
        "course": course,
        "enrollment": enrollment,
        "modules": modules_ui,
        "progress_percent": course_progress(request.user, course)
    })


# ---------------------------------
# VIDEO PLAYER
# ---------------------------------
@login_required
def video_player(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=module.course,
        is_paid=True
    ).first()

    if not enrollment:
        return render(request, "student/access_denied.html")

    previous_modules = Module.objects.filter(
        course=module.course,
        order__lt=module.order
    )

    for prev in previous_modules:
        if not StudentProgress.objects.filter(
            student=request.user,
            module=prev,
            is_completed=True
        ).exists():
            return render(request, "student/access_denied.html")

    return render(request, "student/video_player.html", {
        "module": module,
        "video_url": "/media/sample.mp4"
    })


# ---------------------------------
# COMPLETE MODULE
# ---------------------------------
@login_required
def complete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    progress, _ = StudentProgress.objects.get_or_create(
        student=request.user,
        course=module.course,
        module=module
    )

    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

        Notification.objects.create(
            user=request.user,
            message=f"Module '{module.title}' completed 🎉"
        )

    return redirect("course_detail", course_id=module.course.id)


# ---------------------------------
# ANALYTICS
# ---------------------------------
@login_required
def analytics(request):
    return render(request, "student/analytics.html", {
        "hours_spent": 42,
        "completed_courses": Enrollment.objects.filter(
            student=request.user,
            is_paid=True
        ).count(),
        "average_score": 88
    })


# ---------------------------------
# SETTINGS
# ---------------------------------
@login_required
def settings_page(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST" and request.FILES.get("profile_image"):
        profile.profile_image = request.FILES["profile_image"]
        profile.save()
        return redirect("settings")

    return render(request, "student/settings.html", {
        "profile": profile
    })


# ---------------------------------
# CERTIFICATES
# ---------------------------------
@login_required
def certificates(request):
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_paid=True
    ).select_related("course")

    completed_courses = []

    for enrollment in enrollments:
        total = Module.objects.filter(course=enrollment.course).count()
        completed = StudentProgress.objects.filter(
            student=request.user,
            course=enrollment.course,
            is_completed=True
        ).count()

        if total > 0 and total == completed:
            completed_courses.append(enrollment.course)

    return render(request, "student/certificates.html", {
        "completed_courses": completed_courses
    })


# ---------------------------------
# SIGNUP (EMAIL BASED + AUTO LOGIN)
# ---------------------------------
def signup(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        StudentProfile.objects.get_or_create(user=user)

        login(
            request,
            user,
            backend="student.authentication.EmailBackend"
        )

        return redirect("dashboard")

    return render(request, "student/signup.html")


# ---------------------------------
# LOGOUT
# ---------------------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
