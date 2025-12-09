import pytest
import asyncio
from datetime import datetime, timezone
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus, PaymentProvider
from backend.services.payments.idempotency import IdempotencyService
from backend.services.payments.providers import StripeProvider, RazorpayProvider
from backend.services.payments import PaymentManager
from backend.services.credits_service_v2 import CreditsServiceV2


class TestIdempotencyService:
    """Test idempotency service"""
    
    def test_generate_key(self):
        """Test idempotency key generation"""
        service = IdempotencyService(redis_client=None)
        
        key1 = service.generate_key(
            user_id="user_123",
            operation="create_payment",
            params={"amount": 5000, "currency": "INR"}
        )
        
        # Same params should generate same key
        key2 = service.generate_key(
            user_id="user_123",
            operation="create_payment",
            params={"amount": 5000, "currency": "INR"}
        )
        
        assert key1 == key2
        assert key1.startswith("idempotency:")
    
    @pytest.mark.asyncio
    async def test_check_and_store_memory(self):
        """Test in-memory idempotency check and store"""
        service = IdempotencyService(redis_client=None)
        
        key = "idempotency:test_key_123"
        result = {"payment_id": "pi_123", "status": "created"}
        
        # First call - should return None (new operation)
        cached = await service.check_and_store(key)
        assert cached is None
        
        # Store result
        await service.check_and_store(key, result=result)
        
        # Second call - should return cached result
        cached = await service.check_and_store(key)
        assert cached == result
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        service = IdempotencyService(redis_client=None)
        stats = service.get_stats()
        
        assert stats["backend"] == "memory"
        assert "warning" in stats
        assert stats["ttl_seconds"] == 86400


class TestPaymentProviders:
    """Test payment provider implementations"""
    
    @pytest.mark.asyncio
    async def test_stripe_provider_mock_mode(self):
        """Test Stripe provider in mock mode"""
        provider = StripeProvider(config={}, mock_mode=True)
        
        assert provider.is_mock_mode() == True
        assert provider.get_provider_name() == "stripe"
        
        # Test mock payment intent creation
        from backend.services.payments.providers.base import PaymentIntentRequest
        
        request = PaymentIntentRequest(
            amount_cents=5000,
            currency="INR",
            credits_amount=50,
            user_id="user_123",
            user_email="test@example.com",
            metadata={"package_id": "small"},
            idempotency_key="test_key_123"
        )
        
        response = await provider.create_payment_intent(request)
        
        assert response.success == True
        assert response.provider_intent_id.startswith("pi_mock_")
        assert response.amount_cents == 5000
        assert response.status == "requires_payment_method"
    
    @pytest.mark.asyncio
    async def test_razorpay_provider_mock_mode(self):
        """Test Razorpay provider in mock mode"""
        provider = RazorpayProvider(config={}, mock_mode=True)
        
        assert provider.is_mock_mode() == True
        assert provider.get_provider_name() == "razorpay"
        
        # Test mock order creation
        from backend.services.payments.providers.base import PaymentIntentRequest
        
        request = PaymentIntentRequest(
            amount_cents=10000,
            currency="INR",
            credits_amount=120,
            user_id="user_456",
            user_email="test2@example.com",
            metadata={"package_id": "medium"},
            idempotency_key="test_key_456"
        )
        
        response = await provider.create_payment_intent(request)
        
        assert response.success == True
        assert response.provider_intent_id.startswith("order_mock_")
        assert response.amount_cents == 10000
        assert response.status == "created"


class TestCreditsServiceV2:
    """Test enhanced credits service"""
    
    def test_initialization(self):
        """Test credits service initialization"""
        service = CreditsServiceV2()
        assert service.transactions_enabled == False
    
    @pytest.mark.asyncio
    async def test_add_credits_validation(self):
        """Test add credits input validation"""
        service = CreditsServiceV2()
        
        # Test negative amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.add_credits(
                user_id="user_123",
                amount=-100,
                description="Test",
                transaction_type="purchase"
            )
        
        # Test zero amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.add_credits(
                user_id="user_123",
                amount=0,
                description="Test",
                transaction_type="purchase"
            )
    
    @pytest.mark.asyncio
    async def test_deduct_credits_validation(self):
        """Test deduct credits input validation"""
        service = CreditsServiceV2()
        
        # Test negative amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.deduct_credits(
                user_id="user_123",
                amount=-50,
                description="Test",
                transaction_type="spend"
            )


class TestPaymentIntent:
    """Test PaymentIntent model"""
    
    def test_payment_intent_creation(self):
        """Test payment intent model creation"""
        from backend.models.payment_intent import PaymentIntentMetadata
        
        metadata = PaymentIntentMetadata(
            package_id="small",
            credits_amount=50,
            price_cents=5000,
            user_email="test@example.com",
            client_ip="127.0.0.1"
        )
        
        payment_intent = PaymentIntent(
            id="pi_test_123",
            user_id="user_123",
            provider=PaymentProvider.STRIPE,
            provider_intent_id="pi_stripe_abc",
            amount_cents=5000,
            currency="INR",
            credits_amount=50,
            status=PaymentIntentStatus.PENDING,
            metadata=metadata,
            idempotency_key="idem_key_123"
        )
        
        assert payment_intent.id == "pi_test_123"
        assert payment_intent.provider == PaymentProvider.STRIPE
        assert payment_intent.status == PaymentIntentStatus.PENDING
        assert payment_intent.credits_added == False
    
    def test_status_change_tracking(self):
        """Test status change history tracking"""
        from backend.models.payment_intent import PaymentIntentMetadata
        
        payment_intent = PaymentIntent(
            id="pi_test_456",
            user_id="user_456",
            provider=PaymentProvider.RAZORPAY,
            amount_cents=10000,
            currency="INR",
            credits_amount=120,
            metadata=PaymentIntentMetadata(
                package_id="medium",
                credits_amount=120,
                price_cents=10000,
                user_email="test@example.com"
            ),
            idempotency_key="idem_key_456"
        )
        
        # Add status change
        payment_intent.add_status_change(
            PaymentIntentStatus.PROCESSING,
            reason="Payment initiated"
        )
        
        assert payment_intent.status == PaymentIntentStatus.PROCESSING
        assert len(payment_intent.status_history) == 1
        assert payment_intent.status_history[0]["to_status"] == PaymentIntentStatus.PROCESSING
    
    def test_mark_completed(self):
        """Test marking payment as completed"""
        from backend.models.payment_intent import PaymentIntentMetadata
        
        payment_intent = PaymentIntent(
            id="pi_test_789",
            user_id="user_789",
            provider=PaymentProvider.STRIPE,
            amount_cents=20000,
            currency="INR",
            credits_amount=300,
            metadata=PaymentIntentMetadata(
                package_id="large",
                credits_amount=300,
                price_cents=20000,
                user_email="test@example.com"
            ),
            idempotency_key="idem_key_789"
        )
        
        payment_intent.mark_completed(success=True, reason="Payment successful")
        
        assert payment_intent.status == PaymentIntentStatus.SUCCEEDED
        assert payment_intent.completed_at is not None
        assert len(payment_intent.status_history) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
