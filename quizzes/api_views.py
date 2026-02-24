from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import MicroQuiz


@login_required
@require_GET
def get_micro_quiz(request, module_id):
    """
    GET endpoint to fetch micro-quiz for a module.
    """
    micro_quiz = MicroQuiz.objects.filter(
        module_id=module_id,
        is_active=True
    ).first()
    
    if not micro_quiz:
        return JsonResponse({"error": "No active quiz found"}, status=404)
    
    return JsonResponse({
        "question": micro_quiz.question,
        "option_a": micro_quiz.option_a,
        "option_b": micro_quiz.option_b,
        "option_c": micro_quiz.option_c,
        "option_d": micro_quiz.option_d,
        "trigger_time": micro_quiz.trigger_time
    })


@csrf_exempt
@login_required
@require_POST
def micro_quiz_api(request):
    """
    POST endpoint to check micro-quiz answer.
    Accepts: module_id, answer
    """
    module_id = request.POST.get('module_id') or request.data.get('module_id')
    answer = request.POST.get('answer') or request.data.get('answer')
    
    if not module_id or not answer:
        return JsonResponse({"status": "error", "message": "Missing module_id or answer"}, status=400)
    
    # Get active micro-quiz for module
    micro_quiz = MicroQuiz.objects.filter(
        module_id=module_id,
        is_active=True
    ).first()
    
    if not micro_quiz:
        return JsonResponse({"status": "error", "message": "No active quiz found"}, status=404)
    
    # Check answer correctness
    if answer.upper() == micro_quiz.correct_option.upper():
        return JsonResponse({"status": "correct"})
    
    # Incorrect: increment failure count in session
    session_key = f"micro_quiz_failures_{module_id}"
    failures = request.session.get(session_key, 0)
    request.session[session_key] = failures + 1
    
    return JsonResponse({"status": "incorrect"})
