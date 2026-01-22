import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from .base import BasePaymentGateway

class MockGateway(BasePaymentGateway):
    """
    A mock gateway implementation for local development and testing.
    Simulates successful payment initiation and webhook processing.
    """
    
    def initiate_payment(self, amount: Decimal, currency: str, reference: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Simulate a gateway reference
        gateway_ref = f"mock_{uuid.uuid4().hex[:12]}"
        return {
            "gateway_reference": gateway_ref,
            "status": "PENDING",
            "redirect_url": f"https://mock-gateway.com/pay/{gateway_ref}",
            "amount": amount,
            "currency": currency
        }

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        # Mock verification: always return True for development
        return True

    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Standardize the payload format
        return {
            "gateway_reference": payload.get("id"),
            "external_status": payload.get("status"),
            "event_type": payload.get("event"),
            "amount": payload.get("amount"),
            "raw_data": payload
        }

    def get_payment_status(self, gateway_reference: str) -> str:
        # In mock, let's assume it's always COMPLETED if queried after initiation
        return "COMPLETED"
