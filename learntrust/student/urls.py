from django.urls import path
from . import views
from .api_views import (
    my_courses_api,
    dashboard_api,
    progress_api,
    enrollment_api,
    watch_event_api,
    module_heatmap_api,
)

urlpatterns = [

    # 🔐 AUTH
    path("", views.login_view, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    # 🏠 DASHBOARD
    path("dashboard/", views.dashboard, name="dashboard"),

    # 📚 COURSES
    path("courses/", views.my_courses, name="my_courses"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("module/<int:module_id>/video/", views.video_player, name="video_player"),
    path("module/<int:module_id>/complete/", views.complete_module, name="complete_module"),

    # 📊 EXTRA PAGES
    path("analytics/", views.analytics, name="analytics"),
    path("settings/", views.settings_page, name="settings"),
    path("certificates/", views.certificates, name="certificates"),

    # 🔌 APIs
    path("api/enrollments/", enrollment_api, name="api_enrollments"),
    path("api/my-courses/", my_courses_api, name="api_my_courses"),
    path("api/dashboard/", dashboard_api, name="api_dashboard"),
    path("api/progress/", progress_api, name="api_progress"),
    path("api/watch-event/", watch_event_api, name="api_watch_event"),
    path("api/module-heatmap/<int:module_id>/", module_heatmap_api, name="api_module_heatmap"),

    # 👨‍🏫 TEACHER
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/courses/", views.teacher_course_editor, name="teacher_courses"),
    path("teacher/course/<int:course_id>/", views.teacher_course_editor, name="teacher_course_editor"),
    path("teacher/course/<int:course_id>/analytics/", views.teacher_analytics, name="teacher_analytics"),

    path('test-api/', views.test_api, name='test_api'),
]
