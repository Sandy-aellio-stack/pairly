import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio

# Mock the database initialization to avoid Beanie collection errors
@patch('backend.database.init_db')
@patch('backend.services.presence.start_presence_monitor')
@patch('backend.core.redis_client.redis_client.connect')
def test_imports(mock_redis, mock_presence, mock_db):
    """Test that imports work without database initialization"""
    mock_db.return_value = None
    mock_presence.return_value = None
    mock_redis.return_value = None
    
    from fastapi.testclient import TestClient
    from backend.main import app
    
    return TestClient(app)
from backend.models.user import User, Role
from backend.models.subscription import SubscriptionTier
from backend.models.payment_subscription import (
    UserSubscription,
    SubscriptionProvider,
    SubscriptionStatus
)
from backend.utils.subscription_utils import is_user_subscribed

client = TestClient(app)

# Mock user for testing
mock_user = User(
    email="test@example.com",
    password_hash="hashed_password",
    name="Test User",
    role=Role.FAN,
    credits_balance=100
)

# Mock subscription tier
mock_tier = SubscriptionTier(
    creator_id="creator123",
    name="Premium",
    price_cents=999,
    interval="month",
    metadata={
        "stripe_price_id": "price_test123",
        "razorpay_plan_id": "plan_test123"
    }
)

class TestSubscriptionCreation:
    """Test subscription session creation"""
    
    @patch('backend.routes.subscriptions.get_current_user')
    @patch('backend.routes.subscriptions.SubscriptionTier.get')
    @patch('backend.routes.subscriptions.StripeClient.get_or_create_customer')
    @patch('backend.routes.subscriptions.StripeClient.create_checkout_session')
    @patch('backend.models.payment_subscription.UserSubscription.find_one')
    async def test_create_stripe_session(self, mock_find, mock_checkout, mock_customer, mock_tier_get, mock_user_dep):
        """Test creating a Stripe subscription session"""
        # Setup mocks
        mock_user_dep.return_value = mock_user
        mock_tier_get.return_value = mock_tier
        mock_find.return_value = None  # No existing subscription
        mock_customer.return_value = "cus_test123"
        mock_checkout.return_value = {
            "id": "cs_test123",
            "url": "https://checkout.stripe.com/test",
            "subscription": "sub_test123"
        }
        
        # Make request
        response = client.post(
            "/api/subscriptions/create-session",
            json={
                "tier_id": str(mock_tier.id),
                "provider": "stripe"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "checkout_url" in data
    
    @patch('backend.routes.subscriptions.get_current_user')
    @patch('backend.routes.subscriptions.SubscriptionTier.get')
    @patch('backend.routes.subscriptions.RazorpayClient.create_subscription')
    @patch('backend.models.payment_subscription.UserSubscription.find_one')
    async def test_create_razorpay_session(self, mock_find, mock_razorpay, mock_tier_get, mock_user_dep):
        """Test creating a Razorpay subscription session"""
        # Setup mocks
        mock_user_dep.return_value = mock_user
        mock_tier_get.return_value = mock_tier
        mock_find.return_value = None
        mock_razorpay.return_value = {
            "id": "sub_razorpay123",
            "short_url": "https://rzp.io/test"
        }
        
        # Make request
        response = client.post(
            "/api/subscriptions/create-session",
            json={
                "tier_id": str(mock_tier.id),
                "provider": "razorpay"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription_id" in data
        assert "checkout_url" in data

class TestSubscriptionGating:
    """Test subscription-based content gating integration with feed"""
    
    @patch('backend.utils.subscription_utils.redis_client.get_cached_subscription')
    @patch('backend.models.payment_subscription.UserSubscription.find_one')
    async def test_is_user_subscribed_cached(self, mock_find, mock_cache):
        """Test subscription check with Redis cache hit"""
        mock_cache.return_value = True
        
        result = await is_user_subscribed("user123")
        
        assert result is True
        mock_find.assert_not_called()  # Should not hit database
    
    @patch('backend.utils.subscription_utils.redis_client.get_cached_subscription')
    @patch('backend.utils.subscription_utils.redis_client.cache_subscription')
    @patch('backend.models.payment_subscription.UserSubscription.find_one')
    async def test_is_user_subscribed_db_fallback(self, mock_find, mock_cache_set, mock_cache_get):
        """Test subscription check with database fallback"""
        mock_cache_get.return_value = None  # Cache miss
        mock_find.return_value = UserSubscription(
            user_id="user123",
            tier_id="tier123",
            provider_subscription_id="sub_123",
            provider=SubscriptionProvider.STRIPE,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.now() + timedelta(days=30)
        )
        
        result = await is_user_subscribed("user123")
        
        assert result is True
        mock_find.assert_called_once()
        mock_cache_set.assert_called_once()

class TestWebhookIdempotency:
    """Test webhook handler idempotency"""
    
    @patch('backend.routes.webhooks.redis_client.acquire_lock')
    @patch('backend.routes.webhooks.StripeClient.verify_webhook_signature')
    async def test_stripe_webhook_duplicate(self, mock_verify, mock_lock):
        """Test that duplicate webhook events are ignored"""
        mock_verify.return_value = {
            "id": "evt_test123",
            "type": "invoice.payment_succeeded"
        }
        
        # Simulate lock not acquired (duplicate event)
        mock_lock.return_value.__aenter__ = AsyncMock(return_value=False)
        mock_lock.return_value.__aexit__ = AsyncMock(return_value=None)
        
        response = client.post(
            "/webhooks/stripe",
            json={},
            headers={"stripe-signature": "test_sig"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "duplicate"

class TestSubscriptionCancellation:
    """Test subscription cancellation flow"""
    
    @patch('backend.routes.subscriptions.get_current_user')
    @patch('backend.routes.subscriptions.UserSubscription.get')
    @patch('backend.routes.subscriptions.StripeClient.cancel_subscription')
    async def test_cancel_stripe_subscription(self, mock_stripe_cancel, mock_get_sub, mock_user_dep):
        """Test canceling a Stripe subscription"""
        mock_user_dep.return_value = mock_user
        
        test_subscription = UserSubscription(
            user_id=str(mock_user.id),
            tier_id="tier123",
            provider_subscription_id="sub_stripe123",
            provider=SubscriptionProvider.STRIPE,
            status=SubscriptionStatus.ACTIVE
        )
        mock_get_sub.return_value = test_subscription
        mock_stripe_cancel.return_value = {"cancel_at_period_end": True}
        
        response = client.post(
            f"/api/subscriptions/cancel/{test_subscription.id}"
        )
        
        assert response.status_code == 200
        assert "canceled" in response.json()["message"].lower()

class TestAdminPayouts:
    """Test admin payout functionality"""
    
    @patch('backend.admin.routes.admin_payouts.get_current_user')
    async def test_admin_only_access(self, mock_user_dep):
        """Test that non-admin users cannot access payout endpoints"""
        # Non-admin user
        mock_user_dep.return_value = User(
            email="user@example.com",
            password_hash="hashed_password",
            name="Test User",
            role=Role.FAN
        )
        
        response = client.get("/api/admin/payouts")
        
        assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
