from decimal import Decimal
from django.db.models import Sum
from loans.models import Loan, LoanInstallment
from django.utils import timezone
from .services import AuditService
from .events import AuditEventType

class RiskResult:
    def __init__(self, is_passed, failed_rule_code=None, message=None, metadata=None):
        self.is_passed = is_passed
        self.failed_rule_code = failed_rule_code
        self.message = message
        self.metadata = metadata or {}

class RiskEngineService:
    # Configurable Thresholds
    MAX_ACTIVE_LOANS = 2
    MAX_EXPOSURE = Decimal('5000.00')
    LATE_PAYMENT_THRESHOLD_DAYS = 30
    LATE_PAYMENT_COUNT_THRESHOLD = 0  # No late payments allowed exceeding threshold days

    @classmethod
    def evaluate(cls, application, actor=None):
        """
        Evaluate a loan application against compliance and risk rules.
        """
        user = application.borrower
        results = {}

        # R01: Global Blacklist
        if user.is_blacklisted:
            return cls._finalize_evaluation(
                False, 'USER_BLACKLISTED', "User is on the global blacklist.",
                application, actor, results
            )
        results['R01'] = True

        # R02: Maximum Active Loans
        active_loans_count = Loan.objects.filter(borrower=user, status=Loan.Status.ACTIVE).count()
        if active_loans_count >= cls.MAX_ACTIVE_LOANS:
            return cls._finalize_evaluation(
                False, 'MAX_ACTIVE_LOANS_EXCEEDED', 
                f"User already has {active_loans_count} active loans (limit: {cls.MAX_ACTIVE_LOANS}).",
                application, actor, results
            )
        results['R02'] = True

        # R03: Maximum Outstanding Balance
        current_exposure = Loan.objects.filter(
            borrower=user, 
            status=Loan.Status.ACTIVE
        ).aggregate(total=Sum('principal'))['total'] or Decimal('0')
        
        if (current_exposure + application.amount) > cls.MAX_EXPOSURE:
            return cls._finalize_evaluation(
                False, 'EXPOSURE_LIMIT_REACHED',
                f"Total exposure (${current_exposure + application.amount}) exceeds limit of ${cls.MAX_EXPOSURE}.",
                application, actor, results
            )
        results['R03'] = True

        # R04: Excessive Late Payments
        # Check for any historical installments that were overdue for > threshold days
        late_installments = LoanInstallment.objects.filter(
            loan__borrower=user,
            status=LoanInstallment.Status.OVERDUE,
            due_date__lt=timezone.now().date() - timezone.timedelta(days=cls.LATE_PAYMENT_THRESHOLD_DAYS)
        ).count()

        if late_installments > cls.LATE_PAYMENT_COUNT_THRESHOLD:
             return cls._finalize_evaluation(
                False, 'POOR_REPAYMENT_HISTORY',
                f"User has {late_installments} severely overdue installments.",
                application, actor, results
            )
        results['R04'] = True

        return cls._finalize_evaluation(True, None, "All risk checks passed.", application, actor, results)

    @staticmethod
    def _finalize_evaluation(is_passed, failed_rule_code, message, application, actor, results):
        """
        Helper to log the evaluation and return the result.
        """
        AuditService.log_event(
            actor=actor,
            target=application,
            event_type=AuditEventType.COMPLIANCE_RISK_EVALUATION,
            description=message,
            payload_after={
                "is_passed": is_passed,
                "failed_rule_code": failed_rule_code,
                "rule_results": results
            },
            metadata={"source": "RiskEngineService"}
        )
        return RiskResult(is_passed, failed_rule_code, message, results)
