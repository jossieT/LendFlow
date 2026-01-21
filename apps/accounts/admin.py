from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, KYCProfile, KYCDocument

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'balance', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )

class KYCDocumentInline(admin.TabularInline):
    model = KYCDocument
    extra = 1

@admin.register(KYCProfile)
class KYCProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'id_number', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'full_name', 'id_number']
    inlines = [KYCDocumentInline]

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['profile', 'document_type', 'uploaded_at']
    list_filter = ['document_type']

admin.site.register(User, CustomUserAdmin)