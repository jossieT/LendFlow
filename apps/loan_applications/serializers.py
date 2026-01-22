from rest_framework import serializers
from .models import LoanApplication

class LoanApplicationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            'id', 'product', 'product_name', 'amount', 'term', 
            'status', 'remarks', 'created_at'
        ]
        read_only_fields = ['borrower']
