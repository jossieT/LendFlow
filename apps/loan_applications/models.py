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

class ApplicationDocument(AuditBaseModel):
    class DocType(models.TextChoices):
        BANK_STATEMENT = 'BANK_STATEMENT', 'Bank Statement'
        EMPLOYMENT_VERIF = 'EMPLOYMENT_VERIF', 'Employment Verification'
        OTHER = 'OTHER', 'Other'

    application = models.ForeignKey(
        LoanApplication, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DocType.choices)
    file = models.FileField(upload_to='loan_applications/%Y/%m/%d/')

    def __str__(self):
        return f"{self.get_document_type_display()} for App {self.application.id}"

class StatusHistory(AuditBaseModel):
    application = models.ForeignKey(
        LoanApplication, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    from_status = models.CharField(max_length=20, choices=LoanApplication.Status.choices)
    to_status = models.CharField(max_length=20, choices=LoanApplication.Status.choices)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Status Histories"

    def __str__(self):
        return f"App {self.application.id}: {self.from_status} -> {self.to_status}"
