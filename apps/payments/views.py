import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .gateways.factory import GatewayFactory
from .models import Payment, PaymentGatewayTransaction
from .services.repayment_service import RepaymentAllocationService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """
    Generic webhook view that routes the request to the appropriate gateway 
    logic based on a URL parameter (e.g., /api/payments/webhooks/stripe/).
    """
    
    def post(self, request, provider):
        logger.info(f"Received webhook for provider: {provider}")
        
        try:
            gateway = GatewayFactory.get_gateway(provider.upper())
            payload_data = json.loads(request.body.decode('utf-8'))
            signature = request.headers.get('X-Payload-Signature', '')
            
            # 1. Verify Signature
            if not gateway.verify_webhook_signature(request.body.decode('utf-8'), signature):
                logger.warning(f"Invalid signature for {provider} webhook.")
                return HttpResponse(status=400)
            
            # 2. Extract standardized data
            result = gateway.handle_webhook_payload(payload_data)
            gateway_ref = result.get('gateway_reference')
            
            # 3. Audit the raw transaction
            # Finding the associated Payment record
            payment = Payment.objects.filter(gateway_reference=gateway_ref).first()
            
            if payment:
                PaymentGatewayTransaction.objects.create(
                    payment=payment,
                    action=f"{provider}_webhook_{result.get('event_type')}",
                    raw_response=payload_data,
                    is_success=True
                )
                
                # 4. Trigger Business Logic (e.g., Allocation if COMPLETED)
                if result.get('external_status') == 'SUCCESS':
                    payment.status = Payment.Status.COMPLETED
                    payment.save()
                    RepaymentAllocationService.process_payment(payment)
            
            return HttpResponse(status=200)
            
        except ValueError as e:
            logger.error(f"Gateway factory error: {str(e)}")
            return HttpResponse(status=404)
        except Exception as e:
            logger.exception("Error processing webhook")
            return HttpResponse(status=500)
