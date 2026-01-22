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
    def record_deposit(user, amount, description=''):
        """
        Record manual deposit/funding of the account.
        """
        tx = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='deposit',
            description=description or 'Account cooling'
        )
        user.balance += amount
        user.save()
        return tx

    @staticmethod
    @transaction.atomic
    def record_disbursement(user, amount, loan_id):
        """
        Record loan disbursement into the borrower's account.
        """
        tx = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='disbursement',
            description=f'Disbursement for Loan #{loan_id}'
        )
        user.balance += amount
        user.save()
        return tx

    @staticmethod
    @transaction.atomic
    def record_repayment_charge(user, amount, loan_id):
        """
        Deduct funds from user balance for loan repayment.
        """
        tx = Transaction.objects.create(
            user=user,
            amount=-amount,
            transaction_type='repayment',
            description=f'Repayment for Loan #{loan_id}'
        )
        user.balance -= amount
        user.save()
        return tx
