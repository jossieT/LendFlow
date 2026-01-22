from django.contrib import admin, messages
from .models import LoanApplication
from .services import ApplicationService

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'borrower', 'product', 'amount', 'term', 'status', 'created_at']
    list_filter = ['status', 'product']
    search_fields = ['borrower__username', 'remarks']
    
    # Allow editing status for manual testing, but warn about transitions
    fields = ['borrower', 'product', 'amount', 'term', 'status', 'remarks']
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # If status is manually changed in admin, try to use the service for logic
            try:
                # We skip the service transition if it's a force change, 
                # but for the walkthrough flow, we want the logic to trigger (like disbursal)
                ApplicationService.transition_status(
                    obj, 
                    obj.status, 
                    request.user, 
                    reason="Manual Admin Update"
                )
            except Exception as e:
                messages.error(request, f"Transition failed: {str(e)}")
                # Revert status if transition fails
                obj.status = LoanApplication.objects.get(pk=obj.pk).status
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)
