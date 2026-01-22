from typing import Dict, Type
from .base import BasePaymentGateway
from .mock import MockGateway
from ..models import Payment

class GatewayFactory:
    """
    Service to resolve the correct payment gateway implementation 
    based on the payment method.
    """
    
    _gateways: Dict[str, Type[BasePaymentGateway]] = {
        Payment.Method.STRIPE: MockGateway,  # Placeholder for real StripeGateway
        Payment.Method.MPESA: MockGateway,   # Placeholder for real MpesaGateway
        Payment.Method.WALLET: MockGateway,  # Wallet logic might still use a gateway pattern
        Payment.Method.BANK_TRANSFER: MockGateway
    }
    
    @classmethod
    def get_gateway(cls, method: str) -> BasePaymentGateway:
        gateway_class = cls._gateways.get(method)
        if not gateway_class:
            raise ValueError(f"No gateway implementation found for method: {method}")
        return gateway_class()
