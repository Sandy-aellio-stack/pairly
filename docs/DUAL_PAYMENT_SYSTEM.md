# TrueBond Dual Payment System

## Overview

TrueBond uses a dual-payment provider system to optimize payment processing based on user location:

- **Razorpay**: For users in India
- **Stripe**: For users in all other countries

This approach provides:
- Lower transaction fees for Indian users
- Better local payment method support (UPI, Netbanking, etc. for India)
- Global coverage with Stripe for international users
- Optimized currency handling (INR for India, USD for others)

---

## Architecture

### Provider Selection Flow

```
User initiates checkout
    ↓
Detect user location (IP-based or manual)
    ↓
Is user in India (country_code = 'IN')?
    ↓ Yes                          ↓ No
Razorpay (INR)              Stripe (USD)
    ↓                              ↓
Create payment intent
    ↓
Return client secret to frontend
```

### Location Detection Priority

1. **Manual Provider Selection** (if specified by user)
2. **Country Code** (if provided in request)
3. **IP-Based Detection** (automatic geolocation)
4. **Default to Stripe** (fallback)

---

## Backend Implementation

### File Structure

```
backend/
├── services/
│   ├── location_detector.py          # Location detection service
│   └── payments/
│       ├── manager.py                 # Payment manager (orchestration)
│       └── providers/
│           ├── base.py                # Base provider interface
│           ├── stripe_provider.py     # Stripe implementation
│           └── razorpay_provider.py   # Razorpay implementation
└── routes/
    └── payments.py                    # Payment endpoints
```

### Environment Variables

Add these to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Razorpay Configuration (India)
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx

# Payment System Settings
PAYMENTS_ENABLED=true
PAYMENTS_MOCK_MODE=false  # Set to true for testing without real API calls
```

### API Endpoints

#### 1. Get Payment Packages

```http
GET /api/payments/packages
```

Response:
```json
{
  "packages": {
    "small": {
      "credits": 50,
      "amount_usd": 500,
      "amount_inr": 5000
    },
    "medium": {
      "credits": 120,
      "amount_usd": 1000,
      "amount_inr": 10000
    },
    "large": {
      "credits": 300,
      "amount_usd": 2000,
      "amount_inr": 20000
    }
  },
  "supported_providers": ["stripe", "razorpay"],
  "provider_info": {
    "stripe": {
      "name": "Stripe",
      "currencies": ["USD", "EUR", "GBP"],
      "regions": "Global (excluding India)"
    },
    "razorpay": {
      "name": "Razorpay",
      "currencies": ["INR"],
      "regions": "India"
    }
  }
}
```

#### 2. Detect Payment Provider

```http
POST /api/payments/detect-provider
Authorization: Bearer <token>
```

Response:
```json
{
  "provider": "razorpay",
  "currency": "INR",
  "detected_ip": "1.2.3.4"
}
```

#### 3. Create Checkout Session

```http
POST /api/payments/checkout
Authorization: Bearer <token>
Content-Type: application/json

{
  "package_id": "medium",
  "provider": "razorpay",  // Optional - will auto-detect if not provided
  "country_code": "IN"     // Optional
}
```

Response:
```json
{
  "success": true,
  "provider": "razorpay",
  "payment_intent_id": "pi_xxx",
  "client_secret": "order_xxx",
  "amount_cents": 10000,
  "currency": "INR",
  "credits": 120,
  "requires_action": true,
  "provider_data": {
    "key_id": "rzp_live_xxx",
    "razorpay_order": {...}
  }
}
```

#### 4. Stripe Webhook

```http
POST /api/payments/webhook/stripe
Stripe-Signature: <signature>

{
  "id": "evt_xxx",
  "type": "payment_intent.succeeded",
  ...
}
```

#### 5. Razorpay Webhook

```http
POST /api/payments/webhook/razorpay
X-Razorpay-Signature: <signature>

{
  "event": "payment.captured",
  "payload": {...}
}
```

---

## Frontend Integration

### API Service

```javascript
import { paymentsAPI } from '@/services/api';

// Detect recommended provider
const { provider, currency } = await paymentsAPI.detectProvider();

// Create checkout session
const response = await paymentsAPI.checkout({
  package_id: 'medium',
  provider: 'razorpay', // Optional
  country_code: 'IN'    // Optional
});
```

### Stripe Integration

```javascript
// Load Stripe.js
const stripe = await loadStripe(STRIPE_PUBLISHABLE_KEY);

// Create checkout session
const { client_secret } = await paymentsAPI.checkout({
  package_id: 'medium'
});

// Confirm payment
const { error } = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: {
      email: user.email
    }
  }
});
```

### Razorpay Integration

```javascript
// Load Razorpay
const script = document.createElement('script');
script.src = 'https://checkout.razorpay.com/v1/checkout.js';
document.body.appendChild(script);

// Create checkout session
const response = await paymentsAPI.checkout({
  package_id: 'medium'
});

// Open Razorpay checkout
const options = {
  key: response.provider_data.key_id,
  amount: response.amount_cents,
  currency: response.currency,
  order_id: response.client_secret,
  name: 'TrueBond',
  description: `${response.credits} Credits`,
  handler: function(paymentResponse) {
    // Payment successful
    console.log('Payment successful:', paymentResponse);
  }
};

const rzp = new Razorpay(options);
rzp.open();
```

---

## Testing

### Mock Mode

Both providers support mock mode for testing without real API calls:

```bash
# Enable mock mode
PAYMENTS_MOCK_MODE=true
```

In mock mode:
- No real API calls are made
- Mock payment intents are created
- Webhooks are not validated
- Perfect for development and testing

### Provider-Specific Testing

#### Stripe Test Mode

```bash
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_test_xxx
```

Use Stripe test cards:
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002

#### Razorpay Test Mode

```bash
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=test_xxx
```

Use Razorpay test credentials:
- Test amount: Any amount
- Test cards: Provided by Razorpay documentation

---

## Webhook Configuration

### Stripe Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/api/payments/webhook/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `payment_intent.canceled`
4. Copy webhook secret to `.env`

### Razorpay Webhooks

1. Go to Razorpay Dashboard → Webhooks
2. Add webhook URL: `https://your-domain.com/api/payments/webhook/razorpay`
3. Select events:
   - `payment.captured`
   - `payment.failed`
   - `order.paid`
4. Copy webhook secret to `.env`

---

## Security Features

### Webhook Signature Verification

Both providers verify webhook signatures to prevent tampering:

```python
# Stripe
stripe.Webhook.construct_event(payload, signature, secret)

# Razorpay
expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
is_valid = hmac.compare_digest(expected, signature)
```

### Fraud Detection

- Risk scoring for all transactions
- Device fingerprinting
- IP-based fraud detection
- Automatic transaction blocking for high-risk users

### Idempotency

- Payment intents are idempotent (duplicate requests return same result)
- Webhook events are deduplicated
- Credit fulfillment is idempotent (credits only added once)

---

## Currency Handling

### Package Pricing

```python
CREDIT_PACKAGES = {
    "small": {
        "credits": 50,
        "amount_usd": 500,   # $5.00 USD
        "amount_inr": 5000   # ₹50.00 INR (approximate conversion)
    },
    "medium": {
        "credits": 120,
        "amount_usd": 1000,  # $10.00 USD
        "amount_inr": 10000  # ₹100.00 INR
    },
    "large": {
        "credits": 300,
        "amount_usd": 2000,  # $20.00 USD
        "amount_inr": 20000  # ₹200.00 INR
    }
}
```

### Currency Selection

```python
currency = location_detector.get_currency_for_provider(provider)
# Razorpay → INR
# Stripe → USD

amount_cents = package["amount_inr"] if currency == "INR" else package["amount_usd"]
```

---

## Monitoring & Logging

All payment operations are logged with structured logging:

```python
logger.info(
    "Payment intent created",
    extra={
        "event": "payment_intent_created",
        "payment_intent_id": payment_intent.id,
        "provider": provider,
        "user_id": user.id,
        "amount_cents": amount_cents,
        "currency": currency
    }
)
```

Key metrics to monitor:
- Payment success rate by provider
- Average transaction value by provider
- Failed payment reasons
- Webhook processing latency
- Fraud detection blocks

---

## Troubleshooting

### Provider Not Initialized

**Error**: `Invalid payment provider: razorpay`

**Solution**: Check environment variables:
```bash
# Verify credentials are set
echo $RAZORPAY_KEY_ID
echo $RAZORPAY_KEY_SECRET
```

### Webhook Signature Verification Failed

**Error**: `Signature verification failed`

**Solution**:
1. Verify webhook secret in `.env` matches provider dashboard
2. Check webhook endpoint URL is correct
3. Ensure raw payload is being sent to verification

### Location Detection Not Working

**Error**: Provider always defaults to Stripe

**Solution**:
1. Check IP detection service is accessible
2. Verify user IP is being correctly captured
3. Test with manual provider selection

---

## Production Checklist

- [ ] Set `PAYMENTS_MOCK_MODE=false`
- [ ] Configure Stripe live keys
- [ ] Configure Razorpay live keys
- [ ] Set up Stripe webhooks with live endpoint
- [ ] Set up Razorpay webhooks with live endpoint
- [ ] Test Stripe payment flow end-to-end
- [ ] Test Razorpay payment flow end-to-end
- [ ] Verify webhook signature validation
- [ ] Enable fraud detection
- [ ] Set up payment monitoring alerts
- [ ] Test currency conversion accuracy
- [ ] Verify credit fulfillment logic
- [ ] Test refund flows for both providers

---

## Future Enhancements

1. **Additional Payment Methods**
   - Google Pay / Apple Pay via Stripe
   - UPI Direct via Razorpay
   - Bank transfers

2. **Advanced Location Detection**
   - MaxMind GeoIP2 integration
   - User preference storage
   - Manual country selection

3. **Dynamic Currency Pricing**
   - Real-time currency conversion
   - Multi-currency support
   - Regional pricing optimization

4. **Analytics Dashboard**
   - Revenue by provider
   - Geographic distribution
   - Conversion rates
   - Failed payment analysis
