from django.db import transaction
from ..models import Loan, Transaction

class LoanService:
    @staticmethod
    @transaction.atomic
    def apply_for_loan(user, amount, interest_rate, description=''):
        loan = Loan.objects.create(
            borrower=user,
            amount=amount,
            interest_rate=interest_rate,
            description=description,
            status='pending'
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
