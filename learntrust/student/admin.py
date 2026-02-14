from django.contrib import admin
from .models import *


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'is_active']
    list_filter = ['is_active']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'is_paid', 'enrolled_at']
    list_filter = ['is_paid']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published']
    list_filter = ['course', 'is_published']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'module', 'watch_percent', 'is_completed']
    list_filter = ['is_completed']


@admin.register(WatchEvent)
class WatchEventAdmin(admin.ModelAdmin):
    list_display = ['student', 'module', 'event_type', 'created_at']
    list_filter = ['event_type']
    readonly_fields = ['student', 'module', 'current_time', 'event_type', 'sequence_number', 'token_hash', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student', 'course', 'issued_at', 'is_revoked']
    list_filter = ['is_revoked']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['token_expiry_minutes', 'heartbeat_interval_seconds', 'max_micro_quiz_failures', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow add if no settings exist yet
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
