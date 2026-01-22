from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from .models import Loan, LoanInstallment
from .services import ScheduleGenerator, LoanCalculator

class LoanService:
    @staticmethod
    @transaction.atomic
    def create_loan_from_application(application, user):
        """
        Converts an approved application into an active loan and generates the schedule.
        """
        product = application.product
        loan = Loan.objects.create(
            application=application,
            borrower=application.borrower,
            product=product,
            principal=application.amount,
            interest_rate=product.default_interest_rate,
            interest_type=product.interest_type,
            term=application.term,
            status=Loan.Status.ACTIVE,
            grace_period=getattr(product, 'grace_period', 0), # Assuming product might have these
            penalty_rate=getattr(product, 'penalty_rate', 0),
            penalty_flat_fee=getattr(product, 'penalty_flat_fee', 0),
            created_by=user
        )
        
        LoanService.generate_installments(loan, user)
        return loan

    @staticmethod
    def generate_installments(loan, user):
        """
        Generates and saves installments based on loan interest type.
        """
        if loan.interest_type == 'FLAT':
            schedule = ScheduleGenerator.generate_flat_schedule(loan)
        else:
            schedule = ScheduleGenerator.generate_reducing_schedule(loan)
            
        for data in schedule:
            LoanInstallment.objects.create(
                loan=loan,
                due_date=data['due_date'],
                principal_expected=data['principal'],
                interest_expected=data['interest'],
                created_by=user
            )

    @staticmethod
    @transaction.atomic
    def apply_payment(installment, amount, user):
        """
        Applies a payment to an installment following standard priority: 
        1. Penalty 2. Interest 3. Principal
        """
        amount = Decimal(str(amount))
        
        # 1. Penalty
        penalty_due = installment.penalty_expected - installment.penalty_paid
        pay_penalty = min(amount, penalty_due)
        installment.penalty_paid += pay_penalty
        amount -= pay_penalty
        
        # 2. Interest
        interest_due = installment.interest_expected - installment.interest_paid
        pay_interest = min(amount, interest_due)
        installment.interest_paid += pay_interest
        amount -= pay_interest
        
        # 3. Principal
        principal_due = installment.principal_expected - installment.principal_paid
        pay_principal = min(amount, principal_due)
        installment.principal_paid += pay_principal
        amount -= pay_principal
        
        # Update Status
        total_expected = installment.principal_expected + installment.interest_expected + installment.penalty_expected
        total_paid = installment.principal_paid + installment.interest_paid + installment.penalty_paid
        
        if total_paid >= total_expected:
            installment.status = LoanInstallment.Status.PAID
        elif total_paid > 0:
            installment.status = LoanInstallment.Status.PARTIAL
            
        installment.updated_by = user
        installment.save()
        
        return amount # Return overpayment if any
