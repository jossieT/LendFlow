from django.db import models
from django.conf import settings
from core.abstract_models import AuditBaseModel
from loans.models import Loan, LoanInstallment

class Payment(AuditBaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AUTHORIZED = 'AUTHORIZED', 'Authorized'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    class Method(models.TextChoices):
        WALLET = 'WALLET', 'Internal Wallet'
        STRIPE = 'STRIPE', 'Stripe'
        MPESA = 'MPESA', 'M-Pesa'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments',
        db_index=True
    )
    loan = models.ForeignKey(
        Loan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_index=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=Method.choices
    )
    gateway_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    captured_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} - {self.user.username} (${self.amount})"

class PaymentGatewayTransaction(AuditBaseModel):
    """
    Audit log for low-level interactions with external payment gateways.
    Multiple gateway transactions might be linked to a single Payment intent.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='gateway_transactions'
    )
    action = models.CharField(max_length=50)  # e.g., 'charge.succeeded', 'webhook_received'
    raw_response = models.JSONField()
    is_success = models.BooleanField(default=True)

    def __str__(self):
        return f"GatewayTx {self.id} for Payment {self.payment_id}"

class RepaymentAllocation(AuditBaseModel):
    """
    Details exactly how a payment was shared across installments (Waterfall allocation).
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    installment = models.ForeignKey(
        LoanInstallment,
        on_delete=models.PROTECT,
        related_name='allocations'
    )
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=['payment', 'installment']),
        ]

    def __str__(self):
        return f"Allocation {self.id} for Payment {self.payment_id}"

class PaymentAuditLog(AuditBaseModel):
    """
    Detailed audit log for all payment-related events.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    event_type = models.CharField(max_length=50, db_index=True)  # e.g., 'INITIATED', 'ALLOCATED', 'FAILED'
    from_status = models.CharField(max_length=20, null=True, blank=True)
    to_status = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Audit {self.id} for Payment {self.payment_id}: {self.event_type}"
