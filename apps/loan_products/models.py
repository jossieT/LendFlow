from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.abstract_models import AuditBaseModel

class LoanProduct(AuditBaseModel):
    class InterestType(models.TextChoices):
        FLAT = 'FLAT', 'Flat Interest'
        REDUCING = 'REDUCING', 'Reducing Balance'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    interest_type = models.CharField(
        max_length=20, 
        choices=InterestType.choices, 
        default=InterestType.FLAT
    )
    
    # Amount Constraints
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Term Constraints (in months)
    min_term = models.PositiveIntegerField(help_text="Minimum term in months")
    max_term = models.PositiveIntegerField(help_text="Maximum term in months")
    
    # Rates
    default_interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="Annual interest rate (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    is_active = models.BooleanField(default=True)
    eligibility_criteria = models.JSONField(default=dict, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_amount > self.max_amount:
            raise ValidationError("Minimum amount cannot be greater than maximum amount.")
        if self.min_term > self.max_term:
            raise ValidationError("Minimum term cannot be greater than maximum term.")

    def __str__(self):
        return f"{self.name} ({self.get_interest_type_display()})"

class LoanProductFee(AuditBaseModel):
    class FeeType(models.TextChoices):
        FIXED = 'FIXED', 'Fixed Amount'
        PERCENTAGE = 'PERCENTAGE', 'Percentage of Principal'

    product = models.ForeignKey(
        LoanProduct, 
        on_delete=models.CASCADE, 
        related_name='fees'
    )
    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FeeType.choices, default=FeeType.FIXED)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    is_refundable = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} for {self.product.name}"
