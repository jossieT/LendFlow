import abc
from decimal import Decimal
from typing import Dict, Any, Optional

class BasePaymentGateway(abc.ABC):
    """
    Abstract base class for all payment gateway implementations.
    Ensures a consistent interface for different payment providers.
    """
    
    @abc.abstractmethod
    def initiate_payment(self, amount: Decimal, currency: str, reference: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initiate a payment with the provider.
        Should return a dictionary with gateway-specific data (e.g., redirect URL, token).
        """
        pass

    @abc.abstractmethod
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify that the webhook request actually came from the provider.
        """
        pass

    @abc.abstractmethod
    def handle_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the webhook payload and extract standardized payment information.
        Should return a dictionary with status, reference, and raw data.
        """
        pass

    @abc.abstractmethod
    def get_payment_status(self, gateway_reference: str) -> str:
        """
        Query the gateway for the current status of a payment.
        """
        pass
