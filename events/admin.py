import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import ImmutableLog


@admin.register(ImmutableLog)
class ImmutableLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'event_type', 'created_at', 'current_hash']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username', 'event_type', 'token_hash', 'current_hash']
    readonly_fields = ['user', 'module', 'event_type', 'metadata', 'token_hash', 'previous_hash', 'current_hash', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    actions = ['export_as_csv']
    
    @admin.action(description='Export selected logs to CSV')
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="immutable_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['User', 'Module', 'Event Type', 'Metadata', 'Token Hash', 'Previous Hash', 'Current Hash', 'Created At'])
        
        for log in queryset:
            writer.writerow([
                log.user.username,
                str(log.module) if log.module else '',
                log.event_type,
                str(log.metadata),
                log.token_hash,
                log.previous_hash,
                log.current_hash,
                log.created_at.isoformat()
            ])
        
        return response
