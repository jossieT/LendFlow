from rest_framework import serializers
from .models import Payment, RepaymentAllocation
from loans.models import Loan

class RepaymentAllocationSerializer(serializers.ModelSerializer):
    installment_id = serializers.ReadOnlyField(source='installment.id')
    
    class Meta:
        model = RepaymentAllocation
        fields = [
            'id', 'installment_id', 'principal_amount', 
            'interest_amount', 'penalty_amount', 'fee_amount'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    allocations = RepaymentAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'loan', 'amount', 'currency', 
            'status', 'payment_method', 'gateway_reference', 
            'idempotency_key', 'captured_at', 'allocations'
        ]
        read_only_fields = ['user', 'status', 'captured_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate_loan(self, value):
        # Ensure the loan belongs to the user (unless admin)
        user = self.context['request'].user
        if not user.is_staff and value.borrower != user:
            raise serializers.ValidationError("You can only initiate payments for your own loans.")
        return value
