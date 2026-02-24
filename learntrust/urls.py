"""
URL configuration for learntrust project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from student import views  # ✅ IMPORT STUDENT VIEWS

urlpatterns = [
    # 👨‍💼 CUSTOM ADMIN DASHBOARD (Must be BEFORE Django admin)
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/users/", views.admin_user_management, name="admin_user_management"),
    path("admin/certificates/", views.admin_certificate_governance, name="admin_certificate_governance"),
    path("admin/config/", views.admin_system_config, name="admin_system_config"),
    path("admin/compliance/", views.admin_compliance_audit, name="admin_compliance_audit"),
    
    # 🔧 DJANGO ADMIN
    path('admin/', admin.site.urls),

    # 🔐 Auth: send /login/ to role-choose (student urls provide student/login, teacher/login, etc.)
    path('login/', RedirectView.as_view(url='/', permanent=False), name='login'),

    # 🔓 Logout (CUSTOM LOGOUT VIEW)
    path('logout/', views.logout_view, name='logout'),

    # 🎓 Student panel (includes role_choose at "", student/login, teacher/login, signup, dashboard, etc.)
    path('', include('student.urls')),
    
    # 📜 Certificate verification
    path('', include('certificates.urls')),
    
    # 🧩 Quizzes
    path('', include('quizzes.urls')),
    
    # 📊 Events/Logs
    path('', include('events.urls')),
    
    # 🎥 Streaming/HLS
    path('', include('streaming.urls')),
]

# 🎥 MEDIA FILES (VERY IMPORTANT)
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
