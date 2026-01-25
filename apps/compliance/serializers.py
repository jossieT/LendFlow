from rest_framework import serializers

class UserExposureSerializer(serializers.Serializer):
    borrower_id = serializers.IntegerField(source='borrower')
    username = serializers.CharField()
    total_exposure = serializers.DecimalField(max_digits=12, decimal_places=2)

class DefaultRateSerializer(serializers.Serializer):
    total_disbursed_count = serializers.IntegerField()
    default_count = serializers.IntegerField()
    default_rate = serializers.FloatField()

class LatePaymentSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField()
    borrower_username = serializers.CharField(source='loan__borrower__username')
    days_overdue = serializers.IntegerField()
    amount_overdue = serializers.DecimalField(max_digits=12, decimal_places=2)

class AdminActionReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    timestamp = serializers.DateTimeField(source='created_at')
    admin_user = serializers.CharField(source='actor.username')
    event_type = serializers.CharField()
    target_object = serializers.CharField(source='content_object')
    description = serializers.CharField()
    reason = serializers.JSONField(source='metadata')
