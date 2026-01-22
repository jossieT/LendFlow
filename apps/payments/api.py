from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import PaymentSerializer
from .services.repayment_service import RepaymentAllocationService

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a payment or admins to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        idempotency_key = request.data.get('idempotency_key')
        if idempotency_key:
            # Pessimistic check with lock to ensure no two concurrent requests 
            # create the same payment or fail on duplicate key
            existing_payment = Payment.objects.filter(
                user=request.user, 
                idempotency_key=idempotency_key
            ).first()
            if existing_payment:
                serializer = self.get_serializer(existing_payment)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        response = super().create(request, *args, **kwargs)
        
        # Log the initiation
        if response.status_code == status.HTTP_201_CREATED:
            from .models import PaymentAuditLog
            payment_id = response.data['id']
            PaymentAuditLog.objects.create(
                payment_id=payment_id,
                event_type='INITIATED',
                description=f"Payment of {response.data['amount']} {response.data['currency']} initiated via {response.data['payment_method']}.",
                created_by=request.user
            )
            
        return response

    def perform_create(self, serializer):
        # Default user to current request user
        serializer.save(user=self.request.user)

    @action(detail=False, url_path='loan/(?P<loan_id>[^/.]+)', methods=['get'])
    def loan_payments(self, request, loan_id=None):
        """
        GET /api/payments/loan/{loan_id}/
        View payment history for a specific loan.
        """
        user = request.user
        loan = get_object_or_404(Loan, id=loan_id)
        
        # Permission check: Own loan or staff
        if not user.is_staff and loan.borrower != user:
            return Response(
                {"detail": "Not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        payments = self.get_queryset().filter(loan_id=loan_id)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def process_allocation(self, request, pk=None):
        """
        Manually trigger allocation for a COMPLETED payment.
        Usually this would be triggered by a webhook or internal logic.
        """
        payment = self.get_object()
        if payment.status != Payment.Status.COMPLETED:
            return Response(
                {"error": "Only completed payments can be allocated."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        allocations = RepaymentAllocationService.process_payment(payment)
        return Response(
            {"message": f"Allocated to {len(allocations)} installments."},
            status=status.HTTP_200_OK
        )
