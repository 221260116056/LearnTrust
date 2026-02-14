import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import ImmutableLog


@admin.register(ImmutableLog)
class ImmutableLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'event_type', 'timestamp', 'token_hash']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['user__username', 'event_type', 'token_hash']
    readonly_fields = ['user', 'module', 'event_type', 'timestamp', 'token_hash']
    
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
        writer.writerow(['User', 'Module', 'Event Type', 'Timestamp', 'Token Hash'])
        
        for log in queryset:
            writer.writerow([
                log.user.username,
                str(log.module),
                log.event_type,
                log.timestamp.isoformat(),
                log.token_hash
            ])
        
        return response
