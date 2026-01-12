import logging
import secrets
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime, timezone
from .base import (
    PaymentProviderBase,
    PaymentIntentRequest,
    PaymentIntentResponse,
    WebhookEventData
)

logger = logging.getLogger('payment.provider.razorpay')


class RazorpayProvider(PaymentProviderBase):
    """
    Razorpay payment provider implementation (India).

    Mock Mode: Simulates Razorpay API responses without making real API calls.
    Production Mode: Uses Razorpay SDK for real payment processing.
    """

    def __init__(self, config: Dict[str, Any], mock_mode: bool = False):
        super().__init__(config, mock_mode)
        self.provider_name = "razorpay"
        self.key_id = config.get('key_id', '')
        self.key_secret = config.get('key_secret', '')
        self.webhook_secret = config.get('webhook_secret', '')

        if not mock_mode and not self.key_id:
            logger.warning("Razorpay key_id not configured. Provider will operate in mock mode.")
            self.mock_mode = True

        if not self.mock_mode:
            try:
                import razorpay
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
                logger.info("Razorpay SDK initialized for production mode")
            except ImportError:
                logger.error("Razorpay SDK not installed. Install with: pip install razorpay")
                self.mock_mode = True

        if self.mock_mode:
            logger.info("RazorpayProvider running in MOCK MODE")

    async def create_payment_intent(
        self,
        request: PaymentIntentRequest
    ) -> PaymentIntentResponse:
        """
        Create a Razorpay order (equivalent to payment intent).

        Mock Mode: Returns simulated order.
        Production Mode: Creates real Razorpay Order.
        """
        if self.mock_mode:
            return await self._create_mock_order(request)

        try:
            order_data = {
                "amount": request.amount_cents,
                "currency": request.currency.upper(),
                "notes": {
                    "user_id": request.user_id,
                    "user_email": request.user_email,
                    "credits_amount": str(request.credits_amount),
                    "idempotency_key": request.idempotency_key,
                    **{k: str(v) for k, v in request.metadata.items()}
                }
            }

            order = self.client.order.create(data=order_data)

            logger.info(
                f"Razorpay Order created: {order['id']}",
                extra={
                    "event": "razorpay_order_created",
                    "order_id": order['id'],
                    "amount_cents": request.amount_cents,
                    "user_id": request.user_id
                }
            )

            return PaymentIntentResponse(
                success=True,
                provider_intent_id=order['id'],
                client_secret=order['id'],
                status=order['status'],
                amount_cents=order['amount'],
                currency=order['currency'].lower(),
                requires_action=order['status'] == "created",
                provider_data={
                    "razorpay_order": order,
                    "key_id": self.key_id
                }
            )

        except Exception as e:
            logger.error(f"Razorpay Order creation failed: {e}", exc_info=True)
            return PaymentIntentResponse(
                success=False,
                provider_intent_id="",
                status="failed",
                amount_cents=request.amount_cents,
                currency=request.currency,
                error_message=str(e)
            )

    async def _create_mock_order(
        self,
        request: PaymentIntentRequest
    ) -> PaymentIntentResponse:
        """Create mock Razorpay order (for testing)"""
        mock_order_id = f"order_mock_{secrets.token_hex(12)}"

        logger.info(
            f"MOCK: Razorpay Order created: {mock_order_id}",
            extra={
                "event": "razorpay_mock_order_created",
                "mock_order_id": mock_order_id,
                "amount_cents": request.amount_cents,
                "user_id": request.user_id,
                "mode": "MOCK"
            }
        )

        return PaymentIntentResponse(
            success=True,
            provider_intent_id=mock_order_id,
            client_secret=mock_order_id,
            status="created",
            amount_cents=request.amount_cents,
            currency=request.currency,
            requires_action=True,
            provider_data={
                "mock_mode": True,
                "key_id": "rzp_test_mock",
                "simulated_at": datetime.now(timezone.utc).isoformat()
            }
        )

    async def retrieve_payment_intent(self, provider_intent_id: str) -> PaymentIntentResponse:
        """Retrieve Razorpay order status"""
        if self.mock_mode:
            return PaymentIntentResponse(
                success=True,
                provider_intent_id=provider_intent_id,
                status="paid",
                amount_cents=5000,
                currency="inr",
                provider_data={"mock_mode": True}
            )

        try:
            order = self.client.order.fetch(provider_intent_id)

            status_mapping = {
                "created": "requires_payment_method",
                "attempted": "processing",
                "paid": "succeeded"
            }

            return PaymentIntentResponse(
                success=True,
                provider_intent_id=order['id'],
                client_secret=order['id'],
                status=status_mapping.get(order['status'], order['status']),
                amount_cents=order['amount'],
                currency=order['currency'].lower(),
                provider_data={"razorpay_order": order}
            )
        except Exception as e:
            logger.error(f"Failed to retrieve Razorpay order: {e}")
            return PaymentIntentResponse(
                success=False,
                provider_intent_id=provider_intent_id,
                status="unknown",
                amount_cents=0,
                currency="inr",
                error_message=str(e)
            )

    async def cancel_payment_intent(self, provider_intent_id: str) -> bool:
        """Cancel Razorpay order (not supported directly, orders expire automatically)"""
        if self.mock_mode:
            logger.info(f"MOCK: Canceled Razorpay order: {provider_intent_id}")
            return True

        logger.info(f"Razorpay orders expire automatically, no manual cancellation needed: {provider_intent_id}")
        return True

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Razorpay webhook signature"""
        if self.mock_mode:
            logger.info("MOCK: Webhook signature verification (always True in mock mode)")
            return True

        try:
            webhook_secret = secret or self.webhook_secret
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Razorpay webhook signature verification failed: {e}")
            return False

    async def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEventData:
        """Parse Razorpay webhook event"""
        try:
            event_type = payload.get('event', 'unknown')

            entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = entity.get('order_id', '')
            payment_id = entity.get('id', '')
            status = entity.get('status', 'unknown')
            amount = entity.get('amount', 0)
            currency = entity.get('currency', 'INR')

            status_mapping = {
                "captured": "succeeded",
                "authorized": "processing",
                "failed": "failed",
                "refunded": "refunded"
            }

            return WebhookEventData(
                event_id=payment_id,
                event_type=event_type,
                payment_intent_id=order_id,
                status=status_mapping.get(status, status),
                amount_cents=amount,
                currency=currency.lower(),
                timestamp=datetime.now(timezone.utc),
                raw_data=payload
            )
        except Exception as e:
            logger.error(f"Failed to parse Razorpay webhook: {e}")
            raise
