import hashlib
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Enrollment, StudentProgress, Module, WatchEvent
from events.utils import create_log


# =====================================================
# API — WATCH EVENT
# =====================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def watch_event_api(request):
    """
    Secure watch event logging with sequence validation
    """
    import time
    
    module_id = request.data.get("module_id")
    event_type = request.data.get("event_type")
    sequence_number = request.data.get("sequence_number")
    event_timestamp = request.data.get("timestamp")  # Client timestamp

    if not all([module_id, event_type, sequence_number]):
        return Response({"status": "error", "message": "Missing required fields"}, status=400)

    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({"status": "error", "message": "Module not found"}, status=404)

    # Validate sequence number is strictly increasing
    last_event = WatchEvent.objects.filter(
        student=request.user, 
        module=module
    ).order_by('-sequence_number').first()
    
    if last_event and int(sequence_number) <= last_event.sequence_number:
        return Response({
            "status": "error", 
            "message": f"Sequence number must be greater than {last_event.sequence_number}"
        }, status=400)

    # Validate event timestamp is not older than 30 seconds
    if event_timestamp:
        server_time = time.time()
        time_diff = server_time - float(event_timestamp)
        if time_diff > 30:
            return Response({
                "status": "error", 
                "message": "Event timestamp too old (>30s)"
            }, status=400)

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

    # Create immutable audit log
    create_log(
        user=request.user,
        module=module,
        event_type=f"watch_{event_type}",
        metadata={
            "module_id": module_id,
            "event_type": event_type,
            "sequence_number": sequence_number,
            "token_hash": token_hash
        }
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


# =====================================================
# API — MODULE HEATMAP
# =====================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def module_heatmap_api(request, module_id):
    """
    Return video watch heatmap for a module.
    Only accessible by course instructors or admins.
    """
    from django.shortcuts import get_object_or_404
    from .services import generate_video_heatmap
    
    module = get_object_or_404(Module, id=module_id)
    
    # Check if user is instructor or admin
    is_instructor = hasattr(request.user, 'is_instructor') and request.user.is_instructor
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if not (is_instructor or is_admin):
        return Response({"status": "error", "message": "Permission denied"}, status=403)
    
    heatmap = generate_video_heatmap(module)
    
    # Detect sharp drop-off (>40% decrease)
    drop_off_detected = False
    sorted_buckets = sorted(heatmap.keys(), key=lambda x: int(x))
    
    for i in range(1, len(sorted_buckets)):
        prev_count = heatmap[sorted_buckets[i-1]]
        curr_count = heatmap[sorted_buckets[i]]
        
        if prev_count > 0:
            decrease_percent = ((prev_count - curr_count) / prev_count) * 100
            if decrease_percent > 40:
                drop_off_detected = True
                break
    
    return Response({
        "status": "success",
        "module_id": module_id,
        "heatmap": heatmap,
        "drop_off_detected": drop_off_detected
    })
