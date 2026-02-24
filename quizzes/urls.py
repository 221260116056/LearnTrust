from django.urls import path
from . import api_views

urlpatterns = [
    path('api/micro-quiz/', api_views.micro_quiz_api, name='micro_quiz_api'),
    path('api/module/<int:module_id>/micro-quiz/', api_views.get_micro_quiz, name='get_micro_quiz'),
]
