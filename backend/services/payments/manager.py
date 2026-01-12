import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus, PaymentProvider, PaymentIntentMetadata
from backend.services.payments.providers import (
    PaymentProviderBase,
    StripeProvider,
    RazorpayProvider,
    PaymentIntentRequest,
    PaymentIntentResponse
)
from backend.services.payments.idempotency import get_idempotency_service
from backend.services.credits_service_v2 import CreditsServiceV2
from backend.services.ledger import get_ledger_service
from backend.models.financial_ledger import LedgerEntryType
import os

logger = logging.getLogger('payment.manager')


class PaymentManager:
    """
    Central payment orchestration service.
    
    Responsibilities:
    - Provider-agnostic payment intent creation
    - Idempotency handling
    - Credits fulfillment coordination
    - Webhook processing coordination
    """
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.providers: Dict[str, PaymentProviderBase] = {}
        self.idempotency_service = get_idempotency_service()
        self.credits_service = CreditsServiceV2()
        self.ledger_service = get_ledger_service()
        
        # Initialize providers
        self._initialize_providers()
        
        logger.info(
            f"PaymentManager initialized (mock_mode={mock_mode})",
            extra={
                "mock_mode": mock_mode,
                "providers": list(self.providers.keys())
            }
        )
    
    def _initialize_providers(self):
        """Initialize payment providers based on configuration (Stripe + Razorpay)"""
        # Stripe configuration
        stripe_config = {
            'api_key': os.getenv('STRIPE_SECRET_KEY', ''),
            'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', '')
        }

        # Razorpay configuration
        razorpay_config = {
            'key_id': os.getenv('RAZORPAY_KEY_ID', ''),
            'key_secret': os.getenv('RAZORPAY_KEY_SECRET', ''),
            'webhook_secret': os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
        }

        # Create Stripe provider instance (will auto-detect mock mode if no keys)
        self.providers['stripe'] = StripeProvider(stripe_config, mock_mode=self.mock_mode)

        # Create Razorpay provider instance (will auto-detect mock mode if no keys)
        self.providers['razorpay'] = RazorpayProvider(razorpay_config, mock_mode=self.mock_mode)

        logger.info(
            f"Payment providers initialized",
            extra={
                "stripe_mock": self.providers['stripe'].is_mock_mode(),
                "razorpay_mock": self.providers['razorpay'].is_mock_mode()
            }
        )
    
    def get_provider(self, provider_name: str) -> Optional[PaymentProviderBase]:
        """Get payment provider by name"""
        provider = self.providers.get(provider_name.lower())
        if not provider:
            logger.error(f"Provider not found: {provider_name}")
        return provider
    
    async def create_payment_intent(
        self,
        user_id: str,
        user_email: str,
        provider: str,
        amount_cents: int,
        currency: str,
        credits_amount: int,
        metadata: Dict[str, Any],
        fingerprint_id: Optional[str] = None,
        risk_score: Optional[float] = None
    ) -> PaymentIntent:
        """
        Create a payment intent (provider-agnostic).
        
        Steps:
        1. Generate idempotency key
        2. Check for duplicate request
        3. Create provider payment intent
        4. Store PaymentIntent in database
        5. Return PaymentIntent with client secret
        """
        # Generate internal payment intent ID
        internal_id = f"pi_{secrets.token_hex(16)}"
        
        # Generate idempotency key
        idempotency_params = {
            "amount_cents": amount_cents,
            "currency": currency,
            "credits_amount": credits_amount,
            "provider": provider
        }
        idempotency_key = self.idempotency_service.generate_key(
            user_id=user_id,
            operation="create_payment_intent",
            params=idempotency_params
        )
        
        # Check idempotency
        existing_result = await self.idempotency_service.check_and_store(idempotency_key)
        if existing_result:
            logger.info(
                f"Duplicate payment intent request detected",
                extra={
                    "user_id": user_id,
                    "idempotency_key": idempotency_key,
                    "existing_intent_id": existing_result.get('id')
                }
            )
            # Return existing payment intent
            existing_intent = await PaymentIntent.find_one(
                PaymentIntent.id == existing_result.get('id')
            )
            if existing_intent:
                return existing_intent
        
        # Get provider
        payment_provider = self.get_provider(provider)
        if not payment_provider:
            raise ValueError(f"Invalid payment provider: {provider}")
        
        # Create payment intent with provider
        provider_request = PaymentIntentRequest(
            amount_cents=amount_cents,
            currency=currency,
            credits_amount=credits_amount,
            user_id=user_id,
            user_email=user_email,
            metadata=metadata,
            idempotency_key=idempotency_key
        )
        
        logger.info(
            f"Creating payment intent with {provider}",
            extra={
                "user_id": user_id,
                "amount_cents": amount_cents,
                "credits_amount": credits_amount,
                "provider": provider,
                "mock_mode": payment_provider.is_mock_mode()
            }
        )
        
        provider_response = await payment_provider.create_payment_intent(provider_request)
        
        if not provider_response.success:
            logger.error(
                f"Provider payment intent creation failed",
                extra={
                    "provider": provider,
                    "error": provider_response.error_message
                }
            )
            raise Exception(f"Payment intent creation failed: {provider_response.error_message}")
        
        # Create PaymentIntent model
        payment_intent = PaymentIntent(
            id=internal_id,
            user_id=user_id,
            provider=PaymentProvider(provider.lower()),
            provider_intent_id=provider_response.provider_intent_id,
            provider_client_secret=provider_response.client_secret,
            amount_cents=amount_cents,
            currency=currency,
            credits_amount=credits_amount,
            status=PaymentIntentStatus.PENDING,
            metadata=PaymentIntentMetadata(
                package_id=metadata.get('package_id', 'unknown'),
                credits_amount=credits_amount,
                price_cents=amount_cents,
                user_email=user_email,
                fingerprint_id=fingerprint_id,
                risk_score=risk_score,
                client_ip=metadata.get('client_ip'),
                user_agent=metadata.get('user_agent')
            ),
            idempotency_key=idempotency_key,
            fingerprint_id=fingerprint_id,
            risk_score=risk_score,
            provider_response=provider_response.provider_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Save to database
        await payment_intent.insert()
        
        # Store in idempotency cache
        await self.idempotency_service.check_and_store(
            idempotency_key,
            result={"id": internal_id, "status": "created"}
        )
        
        logger.info(
            f"Payment intent created successfully",
            extra={
                "event": "payment_intent_created",
                "internal_id": internal_id,
                "provider_id": provider_response.provider_intent_id,
                "user_id": user_id,
                "amount_cents": amount_cents,
                "provider": provider
            }
        )
        
        return payment_intent
    
    async def fulfill_payment(
        self,
        payment_intent: PaymentIntent,
        simulate_success: bool = False
    ) -> bool:
        """
        Fulfill payment (add credits to user account).
        
        Called after payment is confirmed (via webhook or manual trigger).
        
        Steps:
        1. Check if credits already added
        2. Add credits via CreditsServiceV2 (with transaction simulation)
        3. Update payment intent status
        """
        if payment_intent.credits_added:
            logger.warning(
                f"Credits already added for payment intent {payment_intent.id}",
                extra={"payment_intent_id": payment_intent.id}
            )
            return True
        
        try:
            # Add credits using CreditsServiceV2
            transaction_id = await self.credits_service.add_credits(
                user_id=payment_intent.user_id,
                amount=payment_intent.credits_amount,
                description=f"Payment {payment_intent.id} - {payment_intent.provider}",
                transaction_type="purchase",
                metadata={
                    "payment_intent_id": payment_intent.id,
                    "provider": payment_intent.provider,
                    "provider_intent_id": payment_intent.provider_intent_id,
                    "amount_cents": payment_intent.amount_cents,
                    "currency": payment_intent.currency
                },
                idempotency_key=f"payment_fulfillment_{payment_intent.id}"
            )
            
            # Record in financial ledger (Phase 8.4)
            try:
                ledger_entry = await self.ledger_service.record_payment(
                    payment_intent_id=payment_intent.id,
                    user_id=payment_intent.user_id,
                    amount_cents=payment_intent.amount_cents,
                    credits_amount=payment_intent.credits_amount,
                    provider=payment_intent.provider
                )
                logger.info(f"Ledger entry created: {ledger_entry.id}")
            except Exception as ledger_error:
                logger.error(f"Failed to create ledger entry: {ledger_error}", exc_info=True)
                # Continue even if ledger fails (can be reconciled later)
            
            # Update payment intent
            payment_intent.credits_added = True
            payment_intent.credits_transaction_id = transaction_id
            payment_intent.mark_completed(success=True, reason="Credits added successfully")
            await payment_intent.save()
            
            logger.info(
                f"Payment fulfilled successfully",
                extra={
                    "event": "payment_fulfilled",
                    "payment_intent_id": payment_intent.id,
                    "user_id": payment_intent.user_id,
                    "credits_amount": payment_intent.credits_amount,
                    "transaction_id": transaction_id
                }
            )
            
            return True
        
        except Exception as e:
            logger.error(
                f"Payment fulfillment failed: {e}",
                extra={
                    "payment_intent_id": payment_intent.id,
                    "user_id": payment_intent.user_id
                },
                exc_info=True
            )
            
            # Update payment intent status
            payment_intent.add_status_change(
                PaymentIntentStatus.FAILED,
                reason=f"Fulfillment error: {str(e)}"
            )
            await payment_intent.save()
            
            return False
    
    async def cancel_payment_intent(self, payment_intent_id: str) -> bool:
        """Cancel a payment intent"""
        payment_intent = await PaymentIntent.find_one(PaymentIntent.id == payment_intent_id)
        
        if not payment_intent:
            logger.error(f"Payment intent not found: {payment_intent_id}")
            return False
        
        if payment_intent.status in [PaymentIntentStatus.SUCCEEDED, PaymentIntentStatus.FAILED]:
            logger.warning(f"Cannot cancel payment intent in status: {payment_intent.status}")
            return False
        
        # Cancel with provider
        provider = self.get_provider(payment_intent.provider)
        if provider:
            await provider.cancel_payment_intent(payment_intent.provider_intent_id)
        
        # Update payment intent
        payment_intent.add_status_change(PaymentIntentStatus.CANCELED, reason="Canceled by user")
        await payment_intent.save()
        
        logger.info(f"Payment intent canceled: {payment_intent_id}")
        return True
    
    async def refund_payment(
        self,
        payment_intent_id: str,
        reason: str = "Refund requested",
        mock_mode: bool = True
    ) -> bool:
        """
        Refund a completed payment (mock mode only in Phase 8.2).
        
        Steps:
        1. Verify payment was successful
        2. Check not already refunded
        3. Deduct credits from user (refund)
        4. Update payment intent status
        """
        payment_intent = await PaymentIntent.find_one(PaymentIntent.id == payment_intent_id)
        
        if not payment_intent:
            logger.error(f"Payment intent not found: {payment_intent_id}")
            return False
        
        if payment_intent.status != PaymentIntentStatus.SUCCEEDED:
            logger.error(f"Cannot refund payment in status: {payment_intent.status}")
            return False
        
        if payment_intent.credits_refunded:
            logger.warning(f"Payment already refunded: {payment_intent_id}")
            return True
        
        if not payment_intent.credits_added:
            logger.error(f"Credits were not added, cannot refund: {payment_intent_id}")
            return False
        
        try:
            # Refund credits (deduct from user)
            refund_transaction_id = await self.credits_service.refund_credits(
                user_id=payment_intent.user_id,
                amount=payment_intent.credits_amount,
                description=f"Refund for payment {payment_intent.id} - {reason}",
                payment_intent_id=payment_intent.id,
                metadata={
                    "payment_intent_id": payment_intent.id,
                    "provider": payment_intent.provider,
                    "provider_intent_id": payment_intent.provider_intent_id,
                    "original_transaction_id": payment_intent.credits_transaction_id,
                    "reason": reason
                },
                idempotency_key=f"payment_refund_{payment_intent.id}"
            )
            
            # Record refund in financial ledger (Phase 8.4)
            try:
                ledger_entry = await self.ledger_service.record_refund(
                    payment_intent_id=payment_intent.id,
                    user_id=payment_intent.user_id,
                    credits_amount=payment_intent.credits_amount
                )
                logger.info(f"Refund ledger entry created: {ledger_entry.id}")
            except Exception as ledger_error:
                logger.error(f"Failed to create refund ledger entry: {ledger_error}", exc_info=True)
            
            # Update payment intent
            payment_intent.credits_refunded = True
            payment_intent.refund_transaction_id = refund_transaction_id
            payment_intent.mark_refunded(reason=reason)
            await payment_intent.save()
            
            logger.info(
                f"Payment refunded successfully",
                extra={
                    "event": "payment_refunded",
                    "payment_intent_id": payment_intent.id,
                    "user_id": payment_intent.user_id,
                    "credits_amount": payment_intent.credits_amount,
                    "refund_transaction_id": refund_transaction_id,
                    "reason": reason,
                    "mock_mode": mock_mode
                }
            )
            
            return True
        
        except Exception as e:
            logger.error(
                f"Payment refund failed: {e}",
                extra={
                    "payment_intent_id": payment_intent.id,
                    "user_id": payment_intent.user_id
                },
                exc_info=True
            )
            return False


# Global instance
_payment_manager: Optional[PaymentManager] = None


def get_payment_manager(mock_mode: bool = True) -> PaymentManager:
    """Get global payment manager instance"""
    global _payment_manager
    if _payment_manager is None:
        _payment_manager = PaymentManager(mock_mode=mock_mode)
    return _payment_manager
