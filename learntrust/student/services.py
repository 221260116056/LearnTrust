from django.utils import timezone
from .models import StudentProgress


def validate_module_unlock(user, module):
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

    return True
