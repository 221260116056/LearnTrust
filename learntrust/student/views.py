from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
import json
from typing import List, Dict, Any, Tuple

try:
    import requests
except ImportError:  # pragma: no cover - handled gracefully if not installed
    requests = None

from .models import (
    Course,
    Enrollment,
    Module,
    StudentProgress,
    StudentProfile,
    Notification
)
from .services import validate_module_unlock

def test_api(request):
    moodle_url = settings.MOODLE_BASE_URL
    token = settings.MOODLE_TOKEN

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat": "json",
    }
    response = requests.get(url, params=params)
    return JsonResponse(response.json(),safe=False)

# ---------------------------------
# HELPER: COURSE PROGRESS %
# ---------------------------------
def course_progress(student, course) -> int:
    """
    Calculate percentage progress for a given course for the student.
    """
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
# HELPER: CONTINUE LEARNING COURSE
# ---------------------------------
def get_continue_course(courses_progress: List[Dict[str, Any]]):
    """
    Pick a 'continue learning' course.

    Strategy:
    - Prefer courses that are in progress (0 < progress < 100), highest progress first.
    - If none are in progress, fall back to the first course (if any).
    """
    in_progress = [
        item for item in courses_progress
        if 0 < (item.get("progress") or 0) < 100
    ]

    if in_progress:
        best = max(in_progress, key=lambda x: x.get("progress") or 0)
    elif courses_progress:
        best = courses_progress[0]
    else:
        return None

    course = best["course"]
    return {
        "title": course.title,
        "progress": best.get("progress") or 0,
        "url": f"/course/{course.id}/",
    }


# ---------------------------------
# HELPER: MOODLE COURSE SYNC
# ---------------------------------
def fetch_moodle_courses(limit: int = 12) -> Tuple[List[Dict[str, Any]], str | None]:
    """
    Fetch a list of courses from Moodle using its REST API.

    Expected settings (configure these in settings.py or environment):
    - MOODLE_BASE_URL  (e.g. https://moodle.example.com)
    - MOODLE_TOKEN     (web service token created in Moodle)

    Returns (courses, error_message)
    - courses: list of lightweight course dicts suitable for the dashboard
    - error_message: None on success, or a short string on failure
    """
    base_url = getattr(settings, "MOODLE_BASE_URL", "").rstrip("/")
    token = getattr(settings, "MOODLE_TOKEN", "")

    if not base_url or not token:
        # Not configured yet – fail silently but surface a friendly message.
        return [], "Moodle connection is not configured yet."

    if requests is None:
        return [], "Python 'requests' package is not installed."

    # Allow either a full server.php URL or just the Moodle root URL.
    if base_url.endswith("/webservice/rest/server.php"):
        endpoint = base_url
    else:
        endpoint = f"{base_url}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat": "json",
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        # Moodle can sometimes return error objects instead of course lists.
        if isinstance(data, dict) and data.get("exception"):
            return [], data.get("message", "Failed to fetch courses from Moodle.")

        # Normal success: list of course dictionaries.
        courses: List[Dict[str, Any]] = []
        for raw in data:
            # Skip special front-page course (id == 1) if present.
            if raw.get("id") == 1:
                continue

            courses.append(
                {
                    "id": raw.get("id"),
                    "shortname": raw.get("shortname") or "",
                    "fullname": raw.get("fullname") or "",
                    "summary": raw.get("summary") or "",
                    "categoryid": raw.get("categoryid"),
                    "url": f"{base_url}/course/view.php?id={raw.get('id')}",
                }
            )

        return courses[:limit], None
    except Exception as exc:  # pragma: no cover - defensive
        # Keep it very short for the UI; detailed logs can go to the console.
        if getattr(settings, "DEBUG", False):
            # This will appear in the Django runserver console.
            print("[Moodle] Error fetching courses:", repr(exc))
        return [], "Unable to reach Moodle at the moment."


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
    enrollments = (
        Enrollment.objects.filter(
            student=request.user,
            is_paid=True,
        )
        .select_related("course")
        .order_by("-enrolled_at")
    )

    courses_progress = [
        {
            "course": enroll.course,
            "progress": course_progress(request.user, enroll.course),
        }
        for enroll in enrollments
    ]

    notifications = (
        Notification.objects.filter(
            user=request.user,
            is_read=False,
        )
        .order_by("-created_at")[:5]
    )

    continue_course = get_continue_course(courses_progress)
    moodle_courses, moodle_error = fetch_moodle_courses()

    return render(
        request,
        "student/dashboard.html",
        {
            "courses_progress": courses_progress,
            "notifications": notifications,
            "continue_course": continue_course,
            "moodle_courses": moodle_courses,
            "moodle_error": moodle_error,
        },
    )


# ---------------------------------
# MY COURSES
# ---------------------------------
@login_required
def my_courses(request):
    enrollments = (
        Enrollment.objects.filter(
            student=request.user,
            is_paid=True,
        )
        .select_related("course")
        .order_by("-enrolled_at")
    )

    courses_progress = [
        {
            "enrollment": enroll,
            "course": enroll.course,
            "progress": course_progress(request.user, enroll.course),
        }
        for enroll in enrollments
    ]

    return render(
        request,
        "student/my_courses.html",
        {
            "courses_progress": courses_progress,
        },
    )


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

        for module in modules:
            completed = progress_qs.filter(
                module=module,
                is_completed=True
            ).exists()

            unlocked = validate_module_unlock(request.user, module)

            modules_ui.append({
                "id": module.id,
                "title": module.title,
                "order": module.order,
                "unlocked": unlocked,
                "completed": completed
            })

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
