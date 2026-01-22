from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from loans.models import Loan, LoanInstallment
from loan_products.models import LoanProduct
from loan_applications.models import LoanApplication
from .models import Payment, RepaymentAllocation
from .services.repayment_service import RepaymentAllocationService

User = get_user_model()

class RepaymentAllocationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Create a product
        self.product = LoanProduct.objects.create(
            name='Test Product',
            min_amount=100, max_amount=1000,
            min_term=1, max_term=12,
            default_interest_rate=10,
            interest_type='FLAT'
        )
        # Create disbursed application
        self.application = LoanApplication.objects.create(
            borrower=self.user,
            product=self.product,
            amount=500,
            term=2,
            status=LoanApplication.Status.DISBURSED,
            created_by=self.user
        )
        # Create Loan
        self.loan = Loan.objects.create(
            application=self.application,
            borrower=self.user,
            product=self.product,
            principal=500,
            interest_rate=10,
            interest_type='FIXED',
            term=2,
            status=Loan.Status.ACTIVE
        )
        # Create 2 installments
        self.inst1 = LoanInstallment.objects.create(
            loan=self.loan,
            due_date='2026-02-22',
            principal_expected=250,
            interest_expected=25,
            penalty_expected=10
        )
        self.inst2 = LoanInstallment.objects.create(
            loan=self.loan,
            due_date='2026-03-22',
            principal_expected=250,
            interest_expected=25,
            penalty_expected=0
        )

    def test_partial_repayment_penalty_only(self):
        """Test that a small payment only covers the penalty first."""
        payment = Payment.objects.create(
            user=self.user,
            loan=self.loan,
            amount=Decimal('5.00'),
            status=Payment.Status.COMPLETED,
            payment_method=Payment.Method.WALLET,
            idempotency_key='key_partial'
        )
        
        RepaymentAllocationService.process_payment(payment)
        
        self.inst1.refresh_from_db()
        self.assertEqual(self.inst1.penalty_paid, Decimal('5.00'))
        self.assertEqual(self.inst1.status, LoanInstallment.Status.PARTIAL)
        
        allocations = RepaymentAllocation.objects.filter(payment=payment)
        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations[0].penalty_amount, Decimal('5.00'))

    def test_full_installment_repayment(self):
        """Test that a payment covering exactly one installment works."""
        total_due = Decimal('285.00') # 10 penalty + 25 interest + 250 principal
        payment = Payment.objects.create(
            user=self.user,
            loan=self.loan,
            amount=total_due,
            status=Payment.Status.COMPLETED,
            payment_method=Payment.Method.WALLET,
            idempotency_key='key_full'
        )
        
        RepaymentAllocationService.process_payment(payment)
        
        self.inst1.refresh_from_db()
        self.assertEqual(self.inst1.status, LoanInstallment.Status.PAID)
        self.assertEqual(self.inst1.penalty_paid, Decimal('10.00'))
        self.assertEqual(self.inst1.interest_paid, Decimal('25.00'))
        self.assertEqual(self.inst1.principal_paid, Decimal('250.00'))

    def test_overpayment_reduces_future_principal(self):
        """Test that overpayment clears all due and added to the last principal."""
        # Total for both installments: (10+25+250) + (0+25+250) = 285 + 275 = 560
        # Overpay by 40 -> 600
        payment = Payment.objects.create(
            user=self.user,
            loan=self.loan,
            amount=Decimal('600.00'),
            status=Payment.Status.COMPLETED,
            payment_method=Payment.Method.WALLET,
            idempotency_key='key_over'
        )
        
        RepaymentAllocationService.process_payment(payment)
        
        self.inst1.refresh_from_db()
        self.inst2.refresh_from_db()
        
        self.assertEqual(self.inst1.status, LoanInstallment.Status.PAID)
        self.assertEqual(self.inst2.status, LoanInstallment.Status.PAID)
        
        # Last installment principal paid should be original principal (250) + overpayment (40)
        self.assertEqual(self.inst2.principal_paid, Decimal('290.00'))
        
        # Check allocations
        allocations = RepaymentAllocation.objects.filter(payment=payment)
        self.assertEqual(allocations.count(), 2)

    def test_payment_not_completed_skips_allocation(self):
        """Test that allocation doesn't run for non-COMPLETED payments."""
        payment = Payment.objects.create(
            user=self.user,
            loan=self.loan,
            amount=Decimal('100.00'),
            status=Payment.Status.PENDING,
            payment_method=Payment.Method.WALLET,
            idempotency_key='key_pending'
        )
        
        allocations = RepaymentAllocationService.process_payment(payment)
        self.assertEqual(len(allocations), 0)
        
        self.inst1.refresh_from_db()
        self.assertEqual(self.inst1.penalty_paid, Decimal('0.00'))

from rest_framework.test import APITestCase, APIClient

class PaymentAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password')
        self.client.force_authenticate(user=self.user)
        
        # Create a product
        self.product = LoanProduct.objects.create(
            name='API Product',
            min_amount=100, max_amount=1000,
            min_term=1, max_term=12,
            default_interest_rate=10,
            interest_type='FLAT'
        )
        # Create application and loan
        self.application = LoanApplication.objects.create(
            borrower=self.user,
            product=self.product,
            amount=500,
            term=2,
            status=LoanApplication.Status.DISBURSED,
            created_by=self.user
        )
        self.loan = Loan.objects.create(
            application=self.application,
            borrower=self.user,
            product=self.product,
            principal=500,
            interest_rate=10,
            interest_type='FLAT',
            term=2,
            status=Loan.Status.ACTIVE
        )

    def test_idempotent_payment_creation(self):
        """Test that sending the same idempotency key twice returns 200 and the same object."""
        data = {
            "loan": self.loan.id,
            "amount": "100.00",
            "payment_method": "STRIPE",
            "idempotency_key": "unique_key_123"
        }
        
        # First request
        response1 = self.client.post('/api/payments/payments/', data)
        self.assertEqual(response1.status_code, 201)
        payment1_id = response1.data['id']
        
        # Second request with same key
        response2 = self.client.post('/api/payments/payments/', data)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data['id'], payment1_id)
        
        # Total payments in DB should still be 1
        self.assertEqual(Payment.objects.filter(user=self.user).count(), 1)
