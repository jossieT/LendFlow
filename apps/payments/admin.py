from django.contrib import admin
from django.utils import timezone
from .models import Payment, PaymentGatewayTransaction, RepaymentAllocation, PaymentAuditLog

class PaymentGatewayTransactionInline(admin.TabularInline):
    model = PaymentGatewayTransaction
    extra = 0
    readonly_fields = ['action', 'raw_response', 'is_success', 'created_at']
    can_delete = False

class RepaymentAllocationInline(admin.TabularInline):
    model = RepaymentAllocation
    extra = 0
    readonly_fields = [
        'installment', 'principal_amount', 'interest_amount', 
        'penalty_amount', 'fee_amount', 'created_at'
    ]
    can_delete = False

class PaymentAuditLogInline(admin.TabularInline):
    model = PaymentAuditLog
    extra = 0
    readonly_fields = ['event_type', 'from_status', 'to_status', 'description', 'metadata', 'created_at']
    can_delete = False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'loan', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'gateway_reference', 'idempotency_key']
    actions = ['process_allocation_action']
    inlines = [PaymentGatewayTransactionInline, RepaymentAllocationInline, PaymentAuditLogInline]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return [
                'user', 'loan', 'amount', 'currency', 'payment_method', 
                'gateway_reference', 'idempotency_key', 'metadata', 'captured_at',
                'created_at', 'updated_at'
            ]
        return ['captured_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Identifiers', {
            'fields': ('idempotency_key', 'gateway_reference', 'user', 'loan')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency', 'payment_method', 'status')
        }),
        ('Timestamps', {
            'fields': ('captured_at', 'created_at', 'updated_at')
        }),
        ('Extra Info', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    def has_change_permission(self, request, obj=None):
        # Prevent manual changes to settled payments (COMPLETED/REFUNDED)
        if obj and obj.status in [Payment.Status.COMPLETED, Payment.Status.REFUNDED]:
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            old_payment = Payment.objects.get(pk=obj.pk)
            if old_payment.status != obj.status:
                # Log status change
                PaymentAuditLog.objects.create(
                    payment=obj,
                    event_type='ADMIN_STATUS_CHANGE',
                    from_status=old_payment.status,
                    to_status=obj.status,
                    description=f"Status manually updated by admin {request.user.username}",
                    created_by=request.user
                )
        super().save_model(request, obj, form, change)

    def process_allocation_action(self, request, queryset):
        success_count = 0
        for payment in queryset:
            if payment.status == Payment.Status.COMPLETED:
                from .services.repayment_service import RepaymentAllocationService
                RepaymentAllocationService.process_payment(payment)
                success_count += 1
        self.message_user(request, f"Successfully processed allocation for {success_count} payments.")
    process_allocation_action.short_description = "Process fund allocation for completed payments"

@admin.register(RepaymentAllocation)
class RepaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ['payment', 'installment', 'principal_amount', 'interest_amount', 'created_at']
    readonly_fields = [f.name for f in RepaymentAllocation._meta.get_fields()]
    
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(PaymentAuditLog)
class PaymentAuditLogAdmin(admin.ModelAdmin):
    list_display = ['payment', 'event_type', 'from_status', 'to_status', 'created_at']
    list_filter = ['event_type', 'created_at']
    readonly_fields = [f.name for f in PaymentAuditLog._meta.get_fields()]

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
