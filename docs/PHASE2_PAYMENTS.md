# Phase 2: Hybrid Payment & Subscription System

## Overview

This document describes the hybrid monetization system that combines:
- **Credits System** (Phase 0): One-time purchases, tips, unlocks
- **Subscription System** (Phase 2): Recurring monthly/yearly subscriptions

Both systems coexist independently. Users can have credits AND subscriptions simultaneously.

## Architecture

### Models
- `UserSubscription`: Tracks user's active/canceled subscriptions
- `PaymentMethod`: Stores payment method metadata from Stripe/Razorpay
- `SubscriptionTier`: Defines creator's subscription offerings (from Phase 1)

### Payment Providers
- **Stripe**: Global payments (card, Apple Pay, Google Pay)
- **Razorpay**: India-focused (UPI, cards, netbanking, wallets)

### Redis Integration
- **Caching**: Subscription status cached for 5 minutes
- **Idempotency**: Webhook events locked for 5 minutes to prevent duplicates

## Environment Variables

Add these to `backend/.env`:

```bash
# Feature Flag
FEATURE_SUBSCRIPTIONS=true

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Razorpay
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

# Redis
REDIS_URL=redis://localhost:6379

# Frontend URL (for checkout redirects)
FRONTEND_URL=http://localhost:3000
```

## Stripe Setup

### 1. Create Products & Prices

```bash
# Create a product
stripe products create \
  --name="Premium Tier" \
  --description="Access to exclusive content"

# Create a recurring price
stripe prices create \
  --product=prod_xxx \
  --unit-amount=999 \
  --currency=usd \
  --recurring[interval]=month
```

### 2. Store Price ID in SubscriptionTier

When creating a tier, add Stripe price_id to metadata:

```python
tier = SubscriptionTier(
    creator_id="creator123",
    name="Premium",
    price_cents=999,
    interval="month",
    metadata={
        "stripe_price_id": "price_xxx"
    }
)
```

### 3. Configure Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/webhooks/stripe`
3. Select events:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

## Razorpay Setup

### 1. Create Plan

```bash
curl -X POST https://api.razorpay.com/v1/plans \
  -u rzp_test_xxx:secret \
  -d period=monthly \
  -d interval=1 \
  -d item[name]="Premium Tier" \
  -d item[amount]=99900 \
  -d item[currency]=INR
```

### 2. Store Plan ID in SubscriptionTier

```python
tier.metadata = {
    "razorpay_plan_id": "plan_xxx"
}
```

### 3. Configure Webhook

1. Go to Razorpay Dashboard → Webhooks
2. Add webhook URL: `https://yourdomain.com/webhooks/razorpay`
3. Select events:
   - `subscription.charged`
   - `subscription.cancelled`
4. Copy webhook secret to `RAZORPAY_WEBHOOK_SECRET`

## API Endpoints

### Create Subscription Session

```bash
POST /api/subscriptions/create-session
Authorization: Bearer <token>

{
  "tier_id": "tier123",
  "provider": "stripe",  # or "razorpay"
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/cancel"
}

Response:
{
  "session_id": "cs_test_xxx",
  "checkout_url": "https://checkout.stripe.com/..."
}
```

### Cancel Subscription

```bash
POST /api/subscriptions/cancel/{subscription_id}
Authorization: Bearer <token>

Response:
{
  "message": "Subscription will be canceled at period end"
}
```

### Get User Subscriptions

```bash
GET /api/subscriptions
Authorization: Bearer <token>

Response:
[
  {
    "id": "sub123",
    "tier_id": "tier123",
    "provider": "stripe",
    "status": "active",
    "current_period_end": "2024-02-01T00:00:00Z"
  }
]
```

### Get Available Tiers

```bash
GET /api/subscriptions/tiers

Response:
[
  {
    "id": "tier123",
    "name": "Premium",
    "price_cents": 999,
    "interval": "month"
  }
]
```

## Webhook Security

### Stripe Signature Verification

All Stripe webhooks are verified using the `stripe-signature` header:

```python
event = stripe.Webhook.construct_event(
    payload, sig_header, STRIPE_WEBHOOK_SECRET
)
```

### Razorpay Signature Verification

Razorpay webhooks use HMAC SHA256:

```python
expected_signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

### Idempotency via Redis

All webhook handlers acquire a distributed lock:

```python
async with redis_client.acquire_lock(f"stripe_webhook:{event_id}"):
    # Process event
```

This prevents duplicate processing if a webhook is retried.

## Admin Payout Instructions

### View Payouts

```bash
GET /api/admin/payouts
Authorization: Bearer <admin_token>
```

### Approve/Reject Payout

```bash
POST /api/admin/payouts/{payout_id}/action
Authorization: Bearer <admin_token>

{
  "action": "approve",  # or "reject"
  "notes": "Approved after verification"
}
```

### Export CSV

```bash
GET /api/admin/payouts/export/csv?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <admin_token>
```

## Migration Steps

### 1. Run Migration Script

```bash
cd /app/backend
python -m migrations.0002_sync_subscription_state
```

This will:
- Create database indexes
- Check for existing subscription data
- Generate migration report

### 2. Manual Verification

- [ ] Check MongoDB indexes exist
- [ ] Verify Redis connection: `redis-cli ping`
- [ ] Test Stripe webhook with CLI: `stripe trigger invoice.payment_succeeded`
- [ ] Test Razorpay webhook with test event
- [ ] Create test subscription end-to-end

### 3. Update SubscriptionTiers

Add price IDs to existing tiers:

```python
tier = await SubscriptionTier.get("tier_id")
tier.metadata["stripe_price_id"] = "price_xxx"
tier.metadata["razorpay_plan_id"] = "plan_xxx"
await tier.save()
```

## Rollback Steps

If you need to rollback Phase 2:

### 1. Disable Feature Flag

```bash
FEATURE_SUBSCRIPTIONS=false
```

### 2. Cancel All Active Subscriptions

```python
subscriptions = await UserSubscription.find(
    {"status": "active"}
).to_list()

for sub in subscriptions:
    if sub.provider == "stripe":
        await StripeClient.cancel_subscription(sub.provider_subscription_id)
    elif sub.provider == "razorpay":
        await RazorpayClient.cancel_subscription(sub.provider_subscription_id)
```

### 3. Remove Collections (Optional)

```javascript
// In MongoDB shell
db.user_subscriptions.drop();
db.payment_methods.drop();
```

### 4. Disable Webhooks

- Stripe Dashboard: Delete webhook endpoint
- Razorpay Dashboard: Delete webhook

## Testing

Run tests:

```bash
pytest backend/tests/test_subscriptions.py -v
```

Test coverage:
- ✅ Subscription creation (Stripe & Razorpay)
- ✅ Webhook idempotency
- ✅ Subscription gating integration with feed
- ✅ Cancellation flow
- ✅ Admin-only payout access

## Troubleshooting

### Webhook Not Received

1. Check webhook URL is publicly accessible
2. Verify webhook secret matches `.env`
3. Check provider dashboard for failed deliveries
4. Test locally with `stripe listen --forward-to localhost:8001/webhooks/stripe`

### Redis Connection Failed

1. Check Redis is running: `redis-cli ping`
2. Verify `REDIS_URL` in `.env`
3. For Docker: ensure Redis container is started

### Subscription Not Gating Content

1. Check Redis cache: `redis-cli GET subscription:user123`
2. Query database directly: `db.user_subscriptions.find({user_id: "user123"})`
3. Verify `current_period_end` is in future
4. Check subscription `status` is `active`

## Performance Considerations

- **Redis Cache TTL**: 5 minutes (adjust in `subscription_utils.py`)
- **Webhook Lock TTL**: 5 minutes (adjust in `webhooks.py`)
- **Database Indexes**: Compound indexes for common queries

## Security Checklist

- [x] Webhook signatures verified
- [x] Idempotency locks prevent duplicate processing
- [x] Admin endpoints require admin role
- [x] API keys stored in environment variables
- [x] User can only cancel their own subscriptions
- [x] Subscription checks use secure queries

## Credits System (Unchanged)

The existing credits system remains fully functional:
- Credit purchases
- Credit transactions
- Post unlocks
- Tips

Subscriptions do NOT affect credits. They are independent systems.
