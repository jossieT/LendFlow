from django.contrib import admin
from .models import LoanApplication, ApplicationDocument, StatusHistory

class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 1

class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    readonly_fields = ['from_status', 'to_status', 'reason', 'created_by', 'created_at']
    can_delete = False
    extra = 0

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'borrower', 'product', 'amount', 'status', 'created_at']
    list_filter = ['status', 'product']
    search_fields = ['borrower__username', 'remarks']
    inlines = [ApplicationDocumentInline, StatusHistoryInline]
    
    fields = ['borrower', 'product', 'amount', 'term', 'status', 'remarks']
    
    def save_model(self, request, obj, form, change):
        from .services import ApplicationService
        from django.contrib import messages
        
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
                # ApplicationService.transition_status already calls application.save()
            except Exception as e:
                messages.error(request, f"Transition failed: {str(e)}")
                # Revert status to old value and save other modified fields if any
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'created_at']

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'from_status', 'to_status', 'created_by', 'created_at']
