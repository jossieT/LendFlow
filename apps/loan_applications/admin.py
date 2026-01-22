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
            new_status = obj.status
            # Revert the object status to original for transition logic in service
            obj.status = form.initial.get('status')
            try:
                ApplicationService.transition_status(
                    obj, 
                    new_status, 
                    request.user, 
                    reason="Manual Admin Update"
                )
                # Note: transition_status already calls application.save()
            except Exception as e:
                messages.error(request, f"Transition failed: {str(e)}")
                # Current obj.status is already the old value
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)
