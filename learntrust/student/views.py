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
from streaming.utils import generate_signed_token

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

    # Generate signed token for secure video streaming
    token = generate_signed_token(request.user.id, module.id)
    
    return render(request, "student/video_player.html", {
        "module": module,
        "video_url": "/media/sample.mp4",
        "token": token
    })


# ---------------------------------
# COMPLETE MODULE
# ---------------------------------
@login_required
def complete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    # Validate module unlock requirements server-side
    if not validate_module_unlock(request.user, module, request):
        return render(request, "student/access_denied.html")
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=module.course,
        is_paid=True
    ).first()
    
    if not enrollment:
        return render(request, "student/access_denied.html")

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


# ---------------------------------
# TEACHER COURSE EDITOR
# ---------------------------------
from .decorators import role_required


@login_required
@role_required('teacher')
def teacher_course_editor(request, course_id=None):
    """
    Teacher course editor for managing modules.
    """
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        modules = Module.objects.filter(course=course).order_by('order')
    else:
        course = None
        modules = []
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_module':
            course_id = request.POST.get('course_id')
            course_obj = get_object_or_404(Course, id=course_id)
            
            # Get max order for this course
            max_order = Module.objects.filter(course=course_obj).count()
            
            Module.objects.create(
                course=course_obj,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                video_url=request.POST.get('video_url', ''),
                order=max_order + 1,
                min_watch_percent=int(request.POST.get('min_watch_percent', 80)),
                must_pass_quiz=request.POST.get('must_pass_quiz') == 'on',
                allowed_attempts=int(request.POST.get('allowed_attempts', 3)),
                disable_seeking=request.POST.get('disable_seeking') == 'on',
                required_replays=int(request.POST.get('required_replays', 0)),
                release_date=request.POST.get('release_date') or None,
                is_published=request.POST.get('is_published') == 'on'
            )
            messages.success(request, "Module added successfully")
            return redirect('teacher_course_editor', course_id=course_id)
        
        elif action == 'edit_module':
            module_id = request.POST.get('module_id')
            module = get_object_or_404(Module, id=module_id)
            
            module.title = request.POST.get('title')
            module.description = request.POST.get('description', '')
            module.video_url = request.POST.get('video_url', '')
            module.min_watch_percent = int(request.POST.get('min_watch_percent', 80))
            module.must_pass_quiz = request.POST.get('must_pass_quiz') == 'on'
            module.allowed_attempts = int(request.POST.get('allowed_attempts', 3))
            module.disable_seeking = request.POST.get('disable_seeking') == 'on'
            module.required_replays = int(request.POST.get('required_replays', 0))
            module.release_date = request.POST.get('release_date') or None
            module.is_published = request.POST.get('is_published') == 'on'
            module.save()
            
            messages.success(request, "Module updated successfully")
            return redirect('teacher_course_editor', course_id=module.course.id)
        
        elif action == 'delete_module':
            module_id = request.POST.get('module_id')
            module = get_object_or_404(Module, id=module_id)
            course_id = module.course.id
            module.delete()
            
            # Reorder remaining modules
            remaining = Module.objects.filter(course_id=course_id).order_by('order')
            for idx, mod in enumerate(remaining, 1):
                mod.order = idx
                mod.save()
            
            messages.success(request, "Module deleted successfully")
            return redirect('teacher_course_editor', course_id=course_id)
        
        elif action == 'reorder_modules':
            module_orders = request.POST.getlist('module_order[]')
            module_ids = request.POST.getlist('module_id[]')
            
            for module_id, order in zip(module_ids, module_orders):
                Module.objects.filter(id=module_id).update(order=int(order))
            
            messages.success(request, "Modules reordered successfully")
            return redirect('teacher_course_editor', course_id=course_id)
    
    courses = Course.objects.filter(is_active=True)
    
    return render(request, 'student/teacher_course_editor.html', {
        'course': course,
        'modules': modules,
        'courses': courses
    })


# ---------------------------------
# TEACHER ANALYTICS DASHBOARD
# ---------------------------------
@login_required
@role_required('teacher')
def teacher_analytics(request, course_id):
    """
    Teacher analytics dashboard showing student progress.
    """
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.filter(course=course).order_by('order')
    
    # Get all enrolled students
    enrollments = Enrollment.objects.filter(
        course=course,
        is_paid=True
    ).select_related('student')
    
    student_data = []
    for enrollment in enrollments:
        student = enrollment.student
        
        # Get progress for all modules
        progress_data = []
        for module in modules:
            progress = StudentProgress.objects.filter(
                student=student,
                module=module
            ).first()
            
            # Count quiz attempts from session
            quiz_attempts = request.session.get(f"quiz_attempts_{student.id}_{module.id}", 0)
            micro_quiz_failures = request.session.get(f"micro_quiz_failures_{module.id}", 0)
            
            progress_data.append({
                'module': module,
                'watch_percent': progress.watch_percent if progress else 0,
                'is_completed': progress.is_completed if progress else False,
                'quiz_attempts': quiz_attempts,
                'micro_quiz_failures': micro_quiz_failures
            })
        
        # Calculate overall completion
        completed_count = sum(1 for p in progress_data if p['is_completed'])
        total_modules = len(modules)
        overall_completion = (completed_count / total_modules * 100) if total_modules > 0 else 0
        
        student_data.append({
            'student': student,
            'progress': progress_data,
            'overall_completion': overall_completion,
            'enrollment_date': enrollment.enrolled_at
        })
    
    return render(request, 'student/teacher_analytics.html', {
        'course': course,
        'modules': modules,
        'student_data': student_data
    })


# ---------------------------------
# ADMIN DASHBOARD
# ---------------------------------
from django.contrib.auth.models import User
from certificates.models import Certificate


@login_required
@role_required('admin')
def admin_dashboard(request):
    """
    Admin dashboard for managing users, roles, and certificates.
    """
    users = User.objects.all().select_related('studentprofile')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_role':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')
            user = get_object_or_404(User, id=user_id)
            
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.role = new_role
            profile.save()
            
            messages.success(request, f"Role updated for {user.username}")
            return redirect('admin_dashboard')
        
        elif action == 'toggle_active':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.is_active = not user.is_active
            user.save()
            
            status = "activated" if user.is_active else "deactivated"
            messages.success(request, f"Account {status} for {user.username}")
            return redirect('admin_dashboard')
        
        elif action == 'revoke_certificate':
            certificate_id = request.POST.get('certificate_id')
            certificate = get_object_or_404(Certificate, id=certificate_id)
            user_name = certificate.student.username
            certificate.is_revoked = True
            certificate.save()
            
            messages.success(request, f"Certificate revoked for {user_name}")
            return redirect('admin_dashboard')
    
    # Get all certificates with related data
    certificates = Certificate.objects.all().select_related('student', 'course')
    
    return render(request, 'student/admin_dashboard.html', {
        'users': users,
        'certificates': certificates,
        'role_choices': StudentProfile.ROLE_CHOICES
    })
