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
    readonly_fields = ['balance']
    actions = ['adjust_balance']

    def adjust_balance(self, request, queryset):
        if getattr(request.user, 'role', '') != 'ADMIN':
             self.message_user(request, "Permission Denied: Only Admins can adjust balances.", level='ERROR')
             return

        from compliance.forms import BalanceAdjustmentForm
        from compliance.services import AuditService
        from compliance.events import AuditEventType
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        from decimal import Decimal

        if 'apply' in request.POST:
            form = BalanceAdjustmentForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data['reason']
                delta = form.cleaned_data['amount_delta']
                count = 0
                for user in queryset:
                    old_balance = user.balance
                    user.balance += delta
                    user.save()
                    
                    AuditService.log_event(
                        actor=request.user,
                        target=user,
                        event_type=AuditEventType.ADMIN_BALANCE_ADJUSTMENT,
                        description=f"Balance adjusted by {delta}. Reason: {reason}",
                        payload_before={"balance": str(old_balance)},
                        payload_after={"balance": str(user.balance)},
                        metadata={"reason": reason, "delta": str(delta)}
                    )
                    count += 1
                
                self.message_user(request, f"Successfully adjusted balance for {count} users.")
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = BalanceAdjustmentForm(initial={'_selected_action': queryset.values_list('pk', flat=True)})

        return render(request, 'admin/confirm_compliance_action.html', {
            'items': queryset,
            'form': form,
            'title': 'Balance Adjustment',
            'action': 'adjust_balance'
        })
    adjust_balance.short_description = "Adjust balance of selected users"

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