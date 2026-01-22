from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'timestamp')
    readonly_fields = ('timestamp',) # Ledger entries should be immutable