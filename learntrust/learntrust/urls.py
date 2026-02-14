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
from django.conf import settings
from django.conf.urls.static import static

from student import views  # ✅ IMPORT STUDENT VIEWS

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 Login (Django built-in)
    path(
        'login/',
        views.login_view if hasattr(views, 'login_view') else
        __import__('django.contrib.auth.views').contrib.auth.views.LoginView.as_view(
            template_name='student/login.html'
        ),
        name='login'
    ),

    # 🔓 Logout (CUSTOM LOGOUT VIEW)
    path('logout/', views.logout_view, name='logout'),

    # 🎓 Student panel
    path('', include('student.urls')),
    
    # 📜 Certificate verification
    path('', include('certificates.urls')),
]

# 🎥 MEDIA FILES (VERY IMPORTANT)
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
