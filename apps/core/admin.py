from django.contrib import admin
from .models import Loan, Transaction

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'borrower', 'amount', 'interest_rate', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('borrower__username', 'description')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'timestamp')
    readonly_fields = ('timestamp',) # Ledger entries should be immutable