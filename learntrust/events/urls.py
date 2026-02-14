from django.urls import path
from . import views

urlpatterns = [
    path('teacher/course/<int:course_id>/export-logs/', views.export_logs, name='export_logs'),
]
