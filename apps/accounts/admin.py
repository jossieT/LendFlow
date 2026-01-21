from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Add our new fields to the admin display
    model = User
    list_display = ['username', 'email', 'balance', 'is_lender', 'is_borrower', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('balance', 'is_lender', 'is_borrower')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('balance', 'is_lender', 'is_borrower')}),
    )

admin.site.register(User, CustomUserAdmin)