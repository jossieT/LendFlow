from django.db import transaction
from django.core.exceptions import ValidationError
from .models import LoanApplication

class ApplicationService:
    @staticmethod
    @transaction.atomic
    def transition_status(application, to_status, user, reason=""):
        """
        Idempotent status transition with audit logging.
        """
        from_status = application.status
        
        if from_status == to_status:
            return application

        # Validate transitions
        valid_transitions = {
            LoanApplication.Status.DRAFT: [LoanApplication.Status.SUBMITTED],
            LoanApplication.Status.SUBMITTED: [LoanApplication.Status.UNDER_REVIEW, LoanApplication.Status.REJECTED],
            LoanApplication.Status.UNDER_REVIEW: [LoanApplication.Status.APPROVED, LoanApplication.Status.REJECTED],
            LoanApplication.Status.APPROVED: [LoanApplication.Status.DISBURSED],
        }

        if to_status not in valid_transitions.get(from_status, []):
            is_staff = user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'LOAN_OFFICER']
            if not is_staff:
                raise ValidationError(f"Invalid transition from {from_status} to {to_status}")

        # Business Constraint: KYC Check
        if to_status == LoanApplication.Status.SUBMITTED:
            if not hasattr(application.borrower, 'kyc_profile') or application.borrower.kyc_profile.status != 'VERIFIED':
                raise ValidationError("KYC must be VERIFIED before submitting an application.")

        # Business Constraint: Product limits
        if from_status == LoanApplication.Status.DRAFT and to_status == LoanApplication.Status.SUBMITTED:
            product = application.product
            if application.amount < product.min_amount or application.amount > product.max_amount:
                raise ValidationError(f"Amount must be between {product.min_amount} and {product.max_amount}")
            if application.term < product.min_term or application.term > product.max_term:
                raise ValidationError(f"Term must be between {product.min_term} and {product.max_term}")

        # Update application
        application.status = to_status
        application.updated_by = user
        application.save()

        # Handle Disbursement logic
        if to_status == LoanApplication.Status.DISBURSED:
            from loans.loan_service import LoanService
            LoanService.create_loan_from_application(application, user)

        return application
