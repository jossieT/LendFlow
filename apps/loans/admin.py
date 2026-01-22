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

@admin.register(LoanInstallment)
class LoanInstallmentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'due_date', 'principal_expected', 'interest_expected', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['loan__borrower__username']
