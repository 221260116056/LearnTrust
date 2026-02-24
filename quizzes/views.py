from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import QuizAttempt, MicroQuiz


@login_required
@require_GET
def start_quiz(request, module_id):
    """
    Start a quiz attempt and store start time.
    """
    # Check if there's an existing incomplete attempt
    existing_attempt = QuizAttempt.objects.filter(
        user=request.user,
        module_id=module_id,
        submitted_at__isnull=True
    ).first()
    
    if existing_attempt:
        return JsonResponse({
            "status": "error",
            "message": "Quiz already in progress",
            "attempt_id": existing_attempt.id,
            "started_at": existing_attempt.started_at.isoformat()
        }, status=400)
    
    # Create new quiz attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        module_id=module_id,
        time_limit_seconds=1800  # 30 minutes default
    )
    
    return JsonResponse({
        "status": "success",
        "attempt_id": attempt.id,
        "started_at": attempt.started_at.isoformat(),
        "time_limit_seconds": attempt.time_limit_seconds
    })


@csrf_exempt
@login_required
@require_POST
def submit_quiz(request):
    """
    Submit quiz answers with server-side time validation.
    """
    import json
    
    attempt_id = request.POST.get('attempt_id')
    answers = request.POST.get('answers')
    
    if not attempt_id:
        return JsonResponse({"status": "error", "message": "Missing attempt_id"}, status=400)
    
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    # Check if already submitted
    if attempt.submitted_at:
        return JsonResponse({"status": "error", "message": "Quiz already submitted"}, status=400)
    
    # Record submission time
    attempt.submitted_at = timezone.now()
    
    # Calculate time taken
    time_taken = (attempt.submitted_at - attempt.started_at).total_seconds()
    
    # Check if time limit exceeded
    if time_taken > attempt.time_limit_seconds:
        attempt.passed = False
        attempt.score = 0
        attempt.save()
        return JsonResponse({
            "status": "failed",
            "message": "Time limit exceeded",
            "time_taken": time_taken,
            "time_limit": attempt.time_limit_seconds
        })
    
    # Process answers and calculate score
    if answers:
        answers_data = json.loads(answers)
        total_questions = len(answers_data)
        correct_count = 0
        
        for answer in answers_data:
            micro_quiz = MicroQuiz.objects.filter(
                id=answer.get('question_id'),
                is_active=True
            ).first()
            
            if micro_quiz and answer.get('selected_option', '').upper() == micro_quiz.correct_option.upper():
                correct_count += 1
        
        attempt.score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
        attempt.passed = attempt.score >= 70  # 70% passing threshold
    
    attempt.save()
    
    return JsonResponse({
        "status": "success" if attempt.passed else "failed",
        "score": attempt.score,
        "passed": attempt.passed,
        "time_taken": time_taken
    })
