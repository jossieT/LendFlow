from django.contrib import admin
from .models import Loan, LoanInstallment

class LoanInstallmentInline(admin.TabularInline):
    model = LoanInstallment
    readonly_fields = ['principal_expected', 'interest_expected', 'penalty_expected']
    extra = 0
    can_delete = False

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['id', 'borrower', 'principal', 'interest_type', 'status', 'is_active', 'disbursement_date']
    list_filter = ['interest_type', 'status', 'is_active']
    search_fields = ['borrower__username', 'principal']
    inlines = [LoanInstallmentInline]
    fields = ['borrower', 'application', 'product', 'principal', 'interest_rate', 'interest_type', 'term', 'status', 'is_active', 'disbursement_date']
    readonly_fields = ['disbursement_date']
    actions = ['write_off_loans']

    def write_off_loans(self, request, queryset):
        # Role Check
        if getattr(request.user, 'role', '') != 'ADMIN':
             self.message_user(request, "Permission Denied: Only Admins can write off loans.", level='ERROR')
             return

        from compliance.forms import AdminActionReasonForm
        from compliance.services import AuditService
        from compliance.events import AuditEventType
        from django.shortcuts import render
        from django.http import HttpResponseRedirect

        if 'apply' in request.POST:
            form = AdminActionReasonForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data['reason']
                count = 0
                for loan in queryset:
                    if loan.status != Loan.Status.CLOSED:
                        loan.status = Loan.Status.CLOSED  # Or a dedicated WRITE_OFF status if added
                        loan.is_active = False
                        loan.save()
                        
                        AuditService.log_event(
                            actor=request.user,
                            target=loan,
                            event_type=AuditEventType.ADMIN_LOAN_WRITE_OFF,
                            description=f"Loan written off by Admin. Reason: {reason}",
                            metadata={"reason": reason}
                        )
                        count += 1
                
                self.message_user(request, f"Successfully wrote off {count} loans.")
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = AdminActionReasonForm(initial={'_selected_action': queryset.values_list('pk', flat=True)})

        return render(request, 'admin/confirm_compliance_action.html', {
            'items': queryset,
            'form': form,
            'title': 'Loan Write-Off',
            'action': 'write_off_loans'
        })
    write_off_loans.short_description = "Write off selected loans (Hard Closure)"

@admin.register(LoanInstallment)
class LoanInstallmentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'due_date', 'principal_expected', 'interest_expected', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['loan__borrower__username']
