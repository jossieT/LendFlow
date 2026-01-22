from rest_framework import serializers
from .models import LoanProduct, LoanProductFee

class LoanProductFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProductFee
        fields = ['id', 'name', 'fee_type', 'amount', 'is_refundable']

class LoanProductSerializer(serializers.ModelSerializer):
    fees = LoanProductFeeSerializer(many=True, read_only=True)

    class Meta:
        model = LoanProduct
        fields = [
            'id', 'name', 'description', 'interest_type', 
            'min_amount', 'max_amount', 'min_term', 'max_term', 
            'default_interest_rate', 'is_active', 'eligibility_criteria', 'fees'
        ]
