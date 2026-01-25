from django.contrib import admin
from .models import AuditLog, Blacklist

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

@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at', 'updated_at', 'revoked_at', 'created_by']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
