import logging
import secrets
from typing import Dict, Any
from datetime import datetime, timezone
from .base import (
    PaymentProviderBase,
    PaymentIntentRequest,
    PaymentIntentResponse,
    WebhookEventData
)

logger = logging.getLogger('payment.provider.stripe')


class StripeProvider(PaymentProviderBase):
    """
    Stripe payment provider implementation.
    
    Mock Mode: Simulates Stripe API responses without making real API calls.
    Production Mode: Uses Stripe SDK for real payment processing.
    """
    
    def __init__(self, config: Dict[str, Any], mock_mode: bool = False):
        super().__init__(config, mock_mode)
        self.provider_name = "stripe"
        self.api_key = config.get('api_key', '')
        self.webhook_secret = config.get('webhook_secret', '')
        
        if not mock_mode and not self.api_key:
            logger.warning("Stripe API key not configured. Provider will operate in mock mode.")
            self.mock_mode = True
        
        # Initialize Stripe SDK in production mode
        if not self.mock_mode:
            try:
                import stripe
                stripe.api_key = self.api_key
                self.stripe = stripe
                logger.info("Stripe SDK initialized for production mode")
            except ImportError:
                logger.error("Stripe SDK not installed. Install with: pip install stripe")
                self.mock_mode = True
        
        if self.mock_mode:
            logger.info("StripeProvider running in MOCK MODE")
    
    async def create_payment_intent(
        self,
        request: PaymentIntentRequest
    ) -> PaymentIntentResponse:
        """
        Create a Stripe payment intent.
        
        Mock Mode: Returns simulated payment intent.
        Production Mode: Creates real Stripe PaymentIntent.
        """
        if self.mock_mode:
            return await self._create_mock_payment_intent(request)
        
        try:
            # Real Stripe API call
            payment_intent = self.stripe.PaymentIntent.create(
                amount=request.amount_cents,
                currency=request.currency.lower(),
                metadata={
                    "user_id": request.user_id,
                    "credits_amount": request.credits_amount,
                    "idempotency_key": request.idempotency_key,
                    **request.metadata
                },
                idempotency_key=request.idempotency_key
            )
            
            logger.info(
                f"Stripe PaymentIntent created: {payment_intent.id}",
                extra={
                    "event": "stripe_payment_intent_created",
                    "payment_intent_id": payment_intent.id,
                    "amount_cents": request.amount_cents,
                    "user_id": request.user_id
                }
            )
            
            return PaymentIntentResponse(
                success=True,
                provider_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                status=payment_intent.status,
                amount_cents=payment_intent.amount,
                currency=payment_intent.currency,
                requires_action=payment_intent.status == "requires_action",
                provider_data={
                    "stripe_payment_intent": payment_intent.to_dict()
                }
            )
        
        except Exception as e:
            logger.error(f"Stripe PaymentIntent creation failed: {e}", exc_info=True)
            return PaymentIntentResponse(
                success=False,
                provider_intent_id="",
                status="failed",
                amount_cents=request.amount_cents,
                currency=request.currency,
                error_message=str(e)
            )
    
    async def _create_mock_payment_intent(
        self,
        request: PaymentIntentRequest
    ) -> PaymentIntentResponse:
        """Create mock Stripe payment intent (for testing)"""
        mock_intent_id = f"pi_mock_{secrets.token_hex(12)}"
        mock_client_secret = f"{mock_intent_id}_secret_{secrets.token_hex(16)}"
        
        logger.info(
            f"MOCK: Stripe PaymentIntent created: {mock_intent_id}",
            extra={
                "event": "stripe_mock_payment_intent_created",
                "mock_intent_id": mock_intent_id,
                "amount_cents": request.amount_cents,
                "user_id": request.user_id,
                "mode": "MOCK"
            }
        )
        
        return PaymentIntentResponse(
            success=True,
            provider_intent_id=mock_intent_id,
            client_secret=mock_client_secret,
            status="requires_payment_method",
            amount_cents=request.amount_cents,
            currency=request.currency,
            requires_action=False,
            provider_data={
                "mock_mode": True,
                "simulated_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def retrieve_payment_intent(self, provider_intent_id: str) -> PaymentIntentResponse:
        """Retrieve Stripe payment intent status"""
        if self.mock_mode:
            return PaymentIntentResponse(
                success=True,
                provider_intent_id=provider_intent_id,
                status="succeeded",
                amount_cents=5000,
                currency="inr",
                provider_data={"mock_mode": True}
            )
        
        try:
            payment_intent = self.stripe.PaymentIntent.retrieve(provider_intent_id)
            return PaymentIntentResponse(
                success=True,
                provider_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                status=payment_intent.status,
                amount_cents=payment_intent.amount,
                currency=payment_intent.currency,
                provider_data={"stripe_payment_intent": payment_intent.to_dict()}
            )
        except Exception as e:
            logger.error(f"Failed to retrieve Stripe payment intent: {e}")
            return PaymentIntentResponse(
                success=False,
                provider_intent_id=provider_intent_id,
                status="unknown",
                amount_cents=0,
                currency="inr",
                error_message=str(e)
            )
    
    async def cancel_payment_intent(self, provider_intent_id: str) -> bool:
        """Cancel Stripe payment intent"""
        if self.mock_mode:
            logger.info(f"MOCK: Canceled Stripe payment intent: {provider_intent_id}")
            return True
        
        try:
            self.stripe.PaymentIntent.cancel(provider_intent_id)
            logger.info(f"Stripe payment intent canceled: {provider_intent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Stripe payment intent: {e}")
            return False
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Stripe webhook signature"""
        if self.mock_mode:
            logger.info("MOCK: Webhook signature verification (always True in mock mode)")
            return True
        
        try:
            self.stripe.Webhook.construct_event(
                payload, signature, secret or self.webhook_secret
            )
            return True
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            return False
    
    async def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEventData:
        """Parse Stripe webhook event"""
        try:
            event_type = payload.get('type', 'unknown')
            event_id = payload.get('id', 'unknown')
            
            # Extract payment intent data
            data_object = payload.get('data', {}).get('object', {})
            payment_intent_id = data_object.get('id', '')
            status = data_object.get('status', 'unknown')
            amount = data_object.get('amount', 0)
            currency = data_object.get('currency', 'inr')
            
            return WebhookEventData(
                event_id=event_id,
                event_type=event_type,
                payment_intent_id=payment_intent_id,
                status=status,
                amount_cents=amount,
                currency=currency,
                timestamp=datetime.now(timezone.utc),
                raw_data=payload
            )
        except Exception as e:
            logger.error(f"Failed to parse Stripe webhook: {e}")
            raise
