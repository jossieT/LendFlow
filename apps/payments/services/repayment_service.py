from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from loans.models import LoanInstallment
from ..models import Payment, RepaymentAllocation

class RepaymentAllocationService:
    @staticmethod
    @transaction.atomic
    def process_payment(payment: Payment):
        """
        Allocates funds from a completed payment to loan installments.
        Waterfall: Penalty -> Interest -> Principal
        """
        # Refetch with lock to prevent race conditions during allocation
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        
        if payment.status != Payment.Status.COMPLETED:
            return []
        
        # Check if already allocated to prevent double-processing
        if RepaymentAllocation.objects.filter(payment=payment).exists():
            return list(payment.allocations.all())

        loan = payment.loan
        if not loan:
            return []
            
        # Lock loan to prevent concurrent status updates or other modifications
        from loans.models import Loan
        loan = Loan.objects.select_for_update().get(pk=loan.pk)

        remaining_funds = Decimal(str(payment.amount))
        allocations = []
        
        # Get all installments for the loan, ordered by due date
        installments = LoanInstallment.objects.filter(
            loan=loan,
        ).exclude(
            status=LoanInstallment.Status.PAID
        ).order_by('due_date').select_for_update()

        try:
            for inst in installments:
                if remaining_funds <= 0:
                    break
                
                penalty_due = max(Decimal('0'), inst.penalty_expected - inst.penalty_paid)
                interest_due = max(Decimal('0'), inst.interest_expected - inst.interest_paid)
                principal_due = max(Decimal('0'), inst.principal_expected - inst.principal_paid)
                
                # Waterfall: Penalty -> Interest -> Principal
                p_alloc = min(remaining_funds, penalty_due)
                remaining_funds -= p_alloc
                
                i_alloc = min(remaining_funds, interest_due)
                remaining_funds -= i_alloc
                
                pr_alloc = min(remaining_funds, principal_due)
                remaining_funds -= pr_alloc
                
                if p_alloc > 0 or i_alloc > 0 or pr_alloc > 0:
                    alloc = RepaymentAllocation.objects.create(
                        payment=payment,
                        installment=inst,
                        penalty_amount=p_alloc,
                        interest_amount=i_alloc,
                        principal_amount=pr_alloc
                    )
                    allocations.append(alloc)
                    inst.apply_funds(p_alloc, i_alloc, pr_alloc)

            # Handle Overpayment (excess funds reduce principal of the last installment)
            if remaining_funds > 0:
                last_inst = LoanInstallment.objects.filter(
                    loan=loan
                ).order_by('-due_date').first()
                
                if last_inst:
                    # Find if we already created an allocation record for this installment in this run
                    existing_alloc = next((a for a in allocations if a.installment_id == last_inst.id), None)
                    if existing_alloc:
                        existing_alloc.principal_amount += remaining_funds
                        existing_alloc.save()
                    else:
                        alloc = RepaymentAllocation.objects.create(
                            payment=payment,
                            installment=last_inst,
                            principal_amount=remaining_funds
                        )
                        allocations.append(alloc)
                    
                    last_inst.apply_funds(0, 0, remaining_funds)
                    remaining_funds = Decimal('0')

            payment.captured_at = timezone.now()
            payment.save()

            # Record successful allocation
            from compliance.services import AuditService
            from compliance.events import AuditEventType
            
            AuditService.log_event(
                actor=None,  # System-triggered
                target=payment,
                event_type=AuditEventType.PAYMENT_ALLOCATED,
                description=f"Successfully allocated {payment.amount} to {len(allocations)} installments.",
                payload_after={"allocation_count": len(allocations)}
            )
            
            return allocations
            
        except Exception as e:
            from compliance.services import AuditService
            from compliance.events import AuditEventType
            
            AuditService.log_event(
                actor=None,
                target=payment,
                event_type=AuditEventType.ALLOCATION_FAILED,
                description=f"Allocation failed: {str(e)}",
                payload_after={"error": str(e)}
            )
            raise e
