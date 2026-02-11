from django.urls import path
from . import views
from .api import (
    my_courses_api,
    dashboard_api,
    progress_api,
    enrollment_api,
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
]
