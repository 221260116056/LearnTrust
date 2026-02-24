from django.utils import timezone
from .models import StudentProgress


def validate_module_unlock(user, module, request=None):
    """
    Validate if a user can unlock a module based on various criteria.
    """
    try:
        progress = StudentProgress.objects.get(student=user, module=module)
        watch_percentage = progress.watch_percent
    except StudentProgress.DoesNotExist:
        watch_percentage = 0

    if watch_percentage < getattr(module, 'minimum_watch_percentage', module.min_watch_percent):
        return False

    if getattr(module, 'must_pass_quiz', False):
        quiz_attempt_passed = False
        try:
            from quizzes.models import QuizAttempt
            quiz_attempt = QuizAttempt.objects.filter(
                user=user,
                module=module,
                passed=True
            ).first()
            if quiz_attempt:
                quiz_attempt_passed = True
        except ImportError:
            pass
        
        if not quiz_attempt_passed:
            return False

    release_date = getattr(module, 'release_date', None)
    if release_date and release_date > timezone.now():
        return False

    allowed_attempts = getattr(module, 'allowed_attempts', None)
    if allowed_attempts is not None:
        try:
            from quizzes.models import QuizAttempt
            attempt_count = QuizAttempt.objects.filter(
                user=user,
                module=module
            ).count()
            if attempt_count >= allowed_attempts:
                return False
        except ImportError:
            pass

    # Check micro-quiz failures
    if request:
        session_key = f"micro_quiz_failures_{module.id}"
        failures = request.session.get(session_key, 0)
        if failures > 3:
            return False

    return True


def generate_video_heatmap(module):
    """
    Generate a heatmap of video watch events grouped into 10-second buckets.
    Returns dictionary with bucket number as key and heartbeat count as value.
    """
    from collections import defaultdict
    from .models import WatchEvent
    
    heatmap = defaultdict(int)
    
    # Fetch all watch events for this module
    events = WatchEvent.objects.filter(module=module, event_type='heartbeat')
    
    # Group events into 10-second buckets
    for event in events:
        bucket = (int(event.current_time) // 10) * 10
        heatmap[bucket] += 1
    
    return dict(heatmap)
