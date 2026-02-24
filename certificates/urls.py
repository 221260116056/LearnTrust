from django.urls import path
from . import views

urlpatterns = [
    path('verify/<uuid:verification_code>/', views.verify_certificate, name='verify_certificate'),
]
