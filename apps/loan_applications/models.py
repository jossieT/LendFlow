from django.db import models
from django.conf import settings
from core.abstract_models import AuditBaseModel
from loan_products.models import LoanProduct

class LoanApplication(AuditBaseModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        DISBURSED = 'DISBURSED', 'Disbursed'

    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='loan_applications'
    )
    product = models.ForeignKey(
        LoanProduct, 
        on_delete=models.PROTECT, 
        related_name='applications'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term = models.PositiveIntegerField(help_text="Term in months")
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.DRAFT
    )
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"App {self.id} - {self.borrower.username} - {self.status}"
