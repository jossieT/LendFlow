from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from compliance.models import AuditLog
from compliance.risk_engine import RiskEngineService
from compliance.events import AuditEventType
from loan_applications.models import LoanApplication
from loan_products.models import LoanProduct
from loans.models import Loan, LoanInstallment

User = get_user_model()

class AuditLogTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password', is_staff=True)
        self.product = LoanProduct.objects.create(
            name="Test Product", 
            min_amount=100, max_amount=10000, 
            min_term=1, max_term=12,
            default_interest_rate=10
        )
        self.app = LoanApplication.objects.create(
            borrower=self.user, 
            product=self.product, 
            amount=500, 
            term=6
        )

    def test_audit_log_immutability(self):
        """Verify that AuditLog records cannot be updated or deleted."""
        log = AuditLog.objects.create(
            actor=self.user,
            content_object=self.app,
            event_type=AuditEventType.LOAN_APPLICATION_SUBMITTED,
            description="Initial log entry"
        )
        
        # Test Update
        with self.assertRaises(ValidationError) as cm:
            log.description = "Updated description"
            log.save()
        self.assertIn("immutable", str(cm.exception))

        # Test Delete
        with self.assertRaises(ValidationError) as cm:
            log.delete()
        self.assertIn("immutable", str(cm.exception))

class RiskEngineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='borrower', password='password')
        self.product = LoanProduct.objects.create(
            name="Test Product", 
            min_amount=100, max_amount=10000, 
            min_term=1, max_term=12,
            default_interest_rate=10
        )
        self.app = LoanApplication.objects.create(
            borrower=self.user, 
            product=self.product, 
            amount=1000, 
            term=6
        )

    def test_r01_blacklist(self):
        """Verify user blacklist check."""
        self.user.is_blacklisted = True
        self.user.save()
        
        result = RiskEngineService.evaluate(self.app)
        self.assertFalse(result.is_passed)
        self.assertEqual(result.failed_rule_code, 'USER_BLACKLISTED')

    def test_r02_max_active_loans(self):
        """Verify maximum active loans limit."""
        # Create 2 active loans with unique applications
        for i in range(2):
            app = LoanApplication.objects.create(
                borrower=self.user,
                product=self.product,
                amount=1000,
                term=6
            )
            Loan.objects.create(
                application=app,
                borrower=self.user,
                product=self.product,
                principal=1000,
                interest_rate=10,
                interest_type='fixed',
                term=6,
                status=Loan.Status.ACTIVE
            )
        
        result = RiskEngineService.evaluate(self.app)
        self.assertFalse(result.is_passed)
        self.assertEqual(result.failed_rule_code, 'MAX_ACTIVE_LOANS_EXCEEDED')

    def test_r03_max_exposure(self):
        """Verify maximum outstanding balance limit."""
        # Create an active loan of $4500 with a unique application
        app = LoanApplication.objects.create(
            borrower=self.user,
            product=self.product,
            amount=4500,
            term=6
        )
        Loan.objects.create(
            application=app,
            borrower=self.user,
            product=self.product,
            principal=4500,
            interest_rate=10,
            interest_type='fixed',
            term=6,
            status=Loan.Status.ACTIVE
        )
        
        # Try to apply for $1000 more (Total $5500 > limit $5000)
        self.app.amount = 1000
        self.app.save()
        
        result = RiskEngineService.evaluate(self.app)
        self.assertFalse(result.is_passed)
        self.assertEqual(result.failed_rule_code, 'EXPOSURE_LIMIT_REACHED')

    def test_r04_late_payments(self):
        """Verify poor repayment history check."""
        loan = Loan.objects.create(
            application=self.app,
            borrower=self.user,
            product=self.product,
            principal=1000,
            interest_rate=10,
            interest_type='fixed',
            term=6,
            status=Loan.Status.ACTIVE
        )
        
        # Create a severely overdue installment
        LoanInstallment.objects.create(
            loan=loan,
            due_date=timezone.now().date() - timezone.timedelta(days=45),
            principal_expected=200,
            interest_expected=20,
            status=LoanInstallment.Status.OVERDUE
        )
        
        result = RiskEngineService.evaluate(self.app)
        self.assertFalse(result.is_passed)
        self.assertEqual(result.failed_rule_code, 'POOR_REPAYMENT_HISTORY')
