from rest_framework import serializers
from .models import LoanApplication, ApplicationDocument, StatusHistory

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ['id', 'document_type', 'file']

class StatusHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StatusHistory
        fields = ['id', 'from_status', 'to_status', 'reason', 'created_at', 'user_name']

class LoanApplicationSerializer(serializers.ModelSerializer):
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            'id', 'product', 'product_name', 'amount', 'term', 
            'status', 'remarks', 'documents', 'status_history'
        ]
        read_only_fields = ['status', 'borrower']

class TransitionSerializer(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=LoanApplication.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
