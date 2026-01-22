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
    
    readonly_fields = ['status'] # Should be changed via services/API

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'created_at']

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'from_status', 'to_status', 'created_by', 'created_at']
