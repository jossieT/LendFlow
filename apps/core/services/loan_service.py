from django.db import transaction
from ..models import Transaction
from loan_applications.models import LoanApplication

class LoanService:
    @staticmethod
    @transaction.atomic
    def apply_for_loan(user, amount, interest_rate, description=''):
        # Legacy shim - create a Draft application
        loan = LoanApplication.objects.create(
            borrower=user,
            amount=amount,
            # interest_rate is handled by LoanProduct, so we ignore it here or map it
            remarks=description,
            status=LoanApplication.Status.DRAFT,
            created_by=user
        )
        return loan

class LedgerService:
    @staticmethod
    @transaction.atomic
    def record_repayment(user, amount, description=''):
        # Create transaction record
        tx = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='repayment',
            description=description
        )
        
        # Update user balance
        user.balance += amount
        user.save()
        
        return tx
