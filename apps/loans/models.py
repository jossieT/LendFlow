from django.db import models
from django.conf import settings
from core.abstract_models import AuditBaseModel
from loan_products.models import LoanProduct
from loan_applications.models import LoanApplication

class Loan(AuditBaseModel):
    application = models.OneToOneField(
        LoanApplication, 
        on_delete=models.CASCADE, 
        related_name='loan_record'
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='loans'
    )
    product = models.ForeignKey(
        LoanProduct, 
        on_delete=models.PROTECT
    )
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAID = 'PAID', 'Paid'
        CLOSED = 'CLOSED', 'Closed'
        DEFAULTED = 'DEFAULTED', 'Defaulted'

    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE
    )
    
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_type = models.CharField(max_length=20)
    term = models.PositiveIntegerField()
    disbursement_date = models.DateTimeField(auto_now_add=True)
    
    # New Fields
    grace_period = models.PositiveIntegerField(default=0, help_text="Number of months of interest-only payments")
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Annual penalty rate for late payments")
    penalty_flat_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Flat fee for late payments")
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Loan {self.id} - {self.borrower.username} (${self.principal})"

    @property
    def amount(self):
        return self.principal

    @property
    def description(self):
        return self.product.description

class LoanInstallment(AuditBaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        PARTIAL = 'PARTIAL', 'Partial'
        OVERDUE = 'OVERDUE', 'Overdue'

    loan = models.ForeignKey(
        Loan, 
        on_delete=models.CASCADE, 
        related_name='installments'
    )
    due_date = models.DateField()
    principal_expected = models.DecimalField(max_digits=12, decimal_places=2)
    interest_expected = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_expected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"Installment {self.id} for Loan {self.loan_id} (Due: {self.due_date})"

    def apply_funds(self, penalty_amount, interest_amount, principal_amount):
        """
        Updates paid amounts and recalculates status.
        """
        from decimal import Decimal
        self.penalty_paid += Decimal(str(penalty_amount))
        self.interest_paid += Decimal(str(interest_amount))
        self.principal_paid += Decimal(str(principal_amount))
        
        total_expected = self.penalty_expected + self.interest_expected + self.principal_expected
        total_paid = self.penalty_paid + self.interest_paid + self.principal_paid
        
        if total_paid >= total_expected:
            self.status = self.Status.PAID
        elif total_paid > 0:
            self.status = self.Status.PARTIAL
        
        self.save()
