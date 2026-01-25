from django.contrib.auth.models import AbstractUser
from django.db import models
from core.abstract_models import AuditBaseModel

class User(AbstractUser):
    class Role(models.TextChoices):
        BORROWER = 'BORROWER', 'Borrower'
        LOAN_OFFICER = 'LOAN_OFFICER', 'Loan Officer'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.BORROWER
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_blacklisted = models.BooleanField(default=False, help_text="If true, the user is barred from applying for new loans.")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class KYCProfile(AuditBaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_profile')
    full_name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return f"KYC for {self.user.username} - {self.status}"

class KYCDocument(AuditBaseModel):
    class DocType(models.TextChoices):
        GOVERNMENT_ID = 'GOVERNMENT_ID', 'Government ID'
        UTILITY_BILL = 'UTILITY_BILL', 'Utility Bill'
        INCOME_PROOF = 'INCOME_PROOF', 'Income Proof'

    profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DocType.choices)
    file = models.FileField(upload_to='kyc_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.profile.user.username}"