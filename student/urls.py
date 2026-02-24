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

    # 🌐 PUBLIC HOME PAGE (Landing page for first-time visitors)
    path("", views.public_home, name="public_home"),
    
    # 🔐 AUTH — role-based (4 pages: student login/signup, teacher login/signup)
    path("role-choose/", views.role_choose, name="role_choose"),
    path("student/login/", views.student_login_view, name="student_login"),
    path("student/signup/", views.student_signup_view, name="student_signup"),
    path("teacher/login/", views.teacher_login_view, name="teacher_login"),
    path("teacher/signup/", views.teacher_signup_view, name="teacher_signup"),
    # Legacy aliases (redirect from role_choose or keep for bookmarks)
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    
    # 🔒 ADMIN PRIVATE AUTH (NO LINKS IN PROJECT - users must type /adminprivate/ manually)
    path("adminprivate/", views.admin_login_view, name="admin_login"),
    
    # 👨‍🏫 TEACHER PENDING APPROVAL
    path("teacher/pending/", views.teacher_pending_approval, name="teacher_pending_approval"),

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
    path("notifications/", views.notifications, name="notifications"),

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
    path("teacher/my-courses/", views.teacher_my_courses_analytics, name="teacher_my_courses"),
    path("teacher/course/<int:course_id>/analytics/", views.teacher_analytics, name="teacher_analytics"),
    path("teacher/logs/", views.teacher_logs, name="teacher_logs"),
    path("teacher/certificates/", views.teacher_certificates, name="teacher_certificates"),
    path("teacher/settings/", views.teacher_settings, name="teacher_settings"),

    path('test-api/', views.test_api, name='test_api'),
    
    # 🌐 PUBLIC PAGES (Before Login)
    path('home/', views.public_home, name='public_home'),
    path('courses-public/', views.public_courses, name='public_courses'),
    path('about/', views.public_about, name='public_about'),
    path('contact/', views.public_contact, name='public_contact'),
]
