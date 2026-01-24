from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'actor', 'event_type', 'content_type', 'object_id']
    list_filter = ['event_type', 'created_at', 'content_type']
    search_fields = ['description', 'actor__username', 'object_id']
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
