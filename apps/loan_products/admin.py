from django.contrib import admin
from .models import LoanProduct, LoanProductFee

class LoanProductFeeInline(admin.TabularInline):
    model = LoanProductFee
    extra = 1

@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'interest_type', 'default_interest_rate', 'is_active', 'min_amount', 'max_amount']
    list_filter = ['interest_type', 'is_active']
    search_fields = ['name', 'description']
    inlines = [LoanProductFeeInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Interest & Constraints', {
            'fields': (('interest_type', 'default_interest_rate'), ('min_amount', 'max_amount'), ('min_term', 'max_term'))
        }),
        ('Advanced', {
            'fields': ('eligibility_criteria',),
            'classes': ('collapse',)
        }),
    )

@admin.register(LoanProductFee)
class LoanProductFeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'fee_type', 'amount', 'is_refundable']
    list_filter = ['fee_type', 'is_refundable']
