from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent"""
    amount_cents: int
    currency: str
    credits_amount: int
    user_id: str
    user_email: str
    metadata: Dict[str, Any]
    idempotency_key: str


class PaymentIntentResponse(BaseModel):
    """Response from payment provider"""
    success: bool
    provider_intent_id: str
    client_secret: Optional[str] = None
    status: str
    amount_cents: int
    currency: str
    requires_action: bool = False
    error_message: Optional[str] = None
    provider_data: Optional[Dict[str, Any]] = None


class WebhookEventData(BaseModel):
    """Parsed webhook event data"""
    event_id: str
    event_type: str
    payment_intent_id: str
    status: str
    amount_cents: int
    currency: str
    timestamp: datetime
    raw_data: Dict[str, Any]


class PaymentProviderBase(ABC):
    """
    Base class for payment providers.
    
    All providers (Stripe, Razorpay, etc.) must implement these methods.
    This enables provider-agnostic payment processing.
    """
    
    def __init__(self, config: Dict[str, Any], mock_mode: bool = False):
        self.config = config
        self.mock_mode = mock_mode
        self.provider_name = "base"
    
    @abstractmethod
    async def create_payment_intent(
        self,
        request: PaymentIntentRequest
    ) -> PaymentIntentResponse:
        """
        Create a payment intent with the provider.
        
        Args:
            request: Payment intent request details
        
        Returns:
            PaymentIntentResponse with provider details
        """
        pass
    
    @abstractmethod
    async def retrieve_payment_intent(self, provider_intent_id: str) -> PaymentIntentResponse:
        """
        Retrieve payment intent status from provider.
        
        Args:
            provider_intent_id: Provider's payment intent ID
        
        Returns:
            Current payment intent status
        """
        pass
    
    @abstractmethod
    async def cancel_payment_intent(self, provider_intent_id: str) -> bool:
        """
        Cancel a payment intent.
        
        Args:
            provider_intent_id: Provider's payment intent ID
        
        Returns:
            True if canceled successfully
        """
        pass
    
    @abstractmethod
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature from provider.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            secret: Webhook signing secret
        
        Returns:
            True if signature is valid
        """
        pass
    
    @abstractmethod
    async def parse_webhook_event(self, payload: Dict[str, Any]) -> WebhookEventData:
        """
        Parse webhook event into standardized format.
        
        Args:
            payload: Webhook payload from provider
        
        Returns:
            Parsed webhook event data
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.mock_mode
