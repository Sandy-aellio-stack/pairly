# Credits System Documentation

## Overview

The Pairly credits system is a virtual currency that enables transactions between users, particularly for messaging, tipping, and premium content access. The system is built with ACID guarantees, idempotency, and comprehensive auditing.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Credits System                         │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Purchase   │  │    Spend     │  │    Refund    │
│  (Add Credits│  │  (Deduct)    │  │  (Reverse)   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                ┌─────────────────┐
                │  MongoDB         │
                │  Transaction     │
                │  (ACID)          │
                └─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ User Balance │  │ Transaction  │  │ Idempotency  │
│ Update       │  │ Ledger       │  │ Check        │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Components

### 1. Credit Ledger Model (`CreditsTransaction`)

**Immutable ledger** recording all credit movements.

```python
class CreditsTransaction(Document):
    user_id: PydanticObjectId
    amount: int  # Positive = added, Negative = spent
    transaction_type: TransactionType
    status: TransactionStatus
    balance_before: int
    balance_after: int
    description: str
    idempotency_key: Optional[str]
    
    # Payment info (for purchases)
    payment_provider: Optional[str]
    payment_id: Optional[str]
    payment_amount_cents: Optional[int]
    
    # Related entities
    related_user_id: Optional[PydanticObjectId]
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]
    
    metadata: Optional[dict]
    created_at: datetime
```

**Transaction Types:**
- `PURCHASE` - User purchased credits
- `ADMIN_GRANT` - Admin manually added
- `REFUND` - Refund from failed transaction
- `BONUS` - Promotional bonus
- `MESSAGE` - Spent on messaging
- `CALL` - Spent on calling
- `TIP` - Tipped a creator
- `UNLOCK` - Unlocked premium content
- `SUBSCRIPTION` - Subscription payment
- `ADMIN_DEDUCT` - Admin penalty
- `EXPIRED` - Credits expired

**Transaction Status:**
- `PENDING` - Initiated but not confirmed
- `COMPLETED` - Successful
- `FAILED` - Transaction failed
- `REVERSED` - Was refunded

### 2. Credits Service (`CreditsService`)

**Core service** managing all credit operations with MongoDB transactions.

**Key Methods:**

#### `add_credits()`
Adds credits to user account.

```python
tx = await CreditsService.add_credits(
    user_id=user_id,
    amount=100,
    transaction_type=TransactionType.PURCHASE,
    description="Purchased starter package",
    idempotency_key="payment_abc123",
    payment_provider="stripe",
    payment_id="pi_123",
    payment_amount_cents=999
)
```

**Features:**
- ACID transaction (MongoDB)
- Idempotency protection
- Automatic balance update
- Immutable ledger entry

#### `spend_credits()`
Spends credits from user account.

```python
tx = await CreditsService.spend_credits(
    user_id=user_id,
    amount=10,
    transaction_type=TransactionType.MESSAGE,
    description="Send message to creator",
    idempotency_key="message_def456",
    related_user_id=creator_id,
    related_entity_type="message",
    related_entity_id="msg_789"
)
```

**Features:**
- Insufficient balance check
- Negative amount in ledger (for spending)
- ACID transaction
- Idempotency protection

#### `refund_credits()`
Reverses a previous transaction.

```python
refund_tx = await CreditsService.refund_credits(
    original_transaction_id="tx_123",
    reason="Payment disputed",
    idempotency_key="refund_456"
)
```

**Features:**
- Reverses original transaction amount
- Marks original as `REVERSED`
- Creates new `REFUND` transaction
- Updates balance

### 3. Credit Routes API

#### **User Endpoints**

**Get Balance**
```http
GET /api/credits/balance
Authorization: Bearer <token>

Response:
{
  "user_id": "507f1f77bcf86cd799439011",
  "credits_balance": 150
}
```

**Get Transaction History**
```http
GET /api/credits/history?limit=50&skip=0
Authorization: Bearer <token>

Response:
{
  "transactions": [
    {
      "id": "tx_123",
      "amount": 100,
      "transaction_type": "purchase",
      "status": "completed",
      "balance_before": 50,
      "balance_after": 150,
      "description": "Purchased starter package",
      "created_at": "2025-12-05T10:30:00Z"
    }
  ],
  "total": 15,
  "limit": 50,
  "skip": 0
}
```

**Get Credit Packages**
```http
GET /api/credits/packages

Response:
{
  "packages": {
    "starter": {
      "credits": 50,
      "price_usd": 4.99,
      "price_inr": 399,
      "bonus_credits": 0,
      "description": "Perfect for trying out"
    },
    "popular": {
      "credits": 120,
      "price_usd": 9.99,
      "price_inr": 799,
      "bonus_credits": 10,
      "description": "Most popular choice"
    }
  }
}
```

#### **Purchase Flow**

**1. Initiate Purchase**
```http
POST /api/credits/purchase/initiate
Authorization: Bearer <token>
Content-Type: application/json

{
  "package_id": "popular",
  "payment_provider": "stripe"
}

Response (Stripe):
{
  "provider": "stripe",
  "client_secret": "pi_abc_secret_xyz",
  "payment_intent_id": "pi_abc123",
  "amount": 9.99,
  "currency": "USD",
  "credits": 130
}

Response (Razorpay):
{
  "provider": "razorpay",
  "order_id": "order_abc123",
  "amount": 799,
  "currency": "INR",
  "credits": 130
}
```

**2. Confirm Purchase**
```http
POST /api/credits/purchase/confirm
Authorization: Bearer <token>
Content-Type: application/json

{
  "payment_id": "pi_abc123",
  "payment_provider": "stripe",
  "package_id": "popular"
}

Response:
{
  "success": true,
  "credits_added": 130,
  "new_balance": 280,
  "transaction_id": "tx_456"
}
```

#### **Spending Credits**

**Spend Credits (Internal)**
```http
POST /api/credits/spend
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 10,
  "transaction_type": "message",
  "description": "Send message",
  "related_user_id": "creator_id",
  "related_entity_type": "message",
  "related_entity_id": "msg_789",
  "idempotency_key": "message_unique_key"
}

Response:
{
  "success": true,
  "credits_spent": 10,
  "new_balance": 140,
  "transaction_id": "tx_789"
}
```

**Tip Creator**
```http
POST /api/credits/tip
Authorization: Bearer <token>
Content-Type: application/json

{
  "creator_id": "507f1f77bcf86cd799439011",
  "amount": 50,
  "message": "Great content!"
}

Response:
{
  "success": true,
  "amount": 50,
  "new_balance": 100,
  "creator_id": "507f1f77bcf86cd799439011"
}
```

#### **Admin Endpoints**

**Adjust Credits**
```http
POST /api/credits/admin/adjust
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": "507f1f77bcf86cd799439011",
  "amount": 50,
  "reason": "Compensation for service disruption",
  "idempotency_key": "admin_adjust_123"
}

Response:
{
  "success": true,
  "user_id": "507f1f77bcf86cd799439011",
  "amount_adjusted": 50,
  "new_balance": 200,
  "transaction_id": "tx_admin_123"
}
```

**Refund Transaction**
```http
POST /api/credits/admin/refund
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "transaction_id": "tx_123",
  "reason": "Disputed payment",
  "idempotency_key": "refund_unique"
}

Response:
{
  "success": true,
  "original_transaction_id": "tx_123",
  "refund_amount": 130,
  "new_balance": 280,
  "refund_transaction_id": "tx_refund_456"
}
```

## Credit Packages

| Package | Credits | Bonus | USD Price | INR Price |
|---------|---------|-------|-----------|-----------|
| Starter | 50 | 0 | $4.99 | ₹399 |
| Popular | 120 | 10 | $9.99 | ₹799 |
| Premium | 300 | 50 | $19.99 | ₹1,599 |
| Ultimate | 1000 | 200 | $49.99 | ₹3,999 |

## Payment Integration

### Stripe Integration

**Setup:**
```bash
pip install stripe
export STRIPE_SECRET_KEY=sk_test_...
```

**Flow:**
1. User initiates purchase → Create PaymentIntent
2. Frontend completes payment with Stripe.js
3. Webhook confirms payment → Add credits
4. Credits added with idempotency

### Razorpay Integration

**Setup:**
```bash
pip install razorpay
export RAZORPAY_KEY_ID=rzp_test_...
export RAZORPAY_KEY_SECRET=...
```

**Flow:**
1. User initiates purchase → Create Order
2. Frontend completes payment with Razorpay SDK
3. Webhook confirms payment → Add credits
4. Credits added with idempotency

## Idempotency

**All operations support idempotency keys** to prevent duplicate transactions.

```python
# Idempotency key prevents duplicate charges
tx = await CreditsService.add_credits(
    user_id=user_id,
    amount=100,
    transaction_type=TransactionType.PURCHASE,
    description="Purchase",
    idempotency_key="unique_payment_id_123"  # ← Key
)

# Second call with same key returns existing transaction
tx2 = await CreditsService.add_credits(
    user_id=user_id,
    amount=100,
    transaction_type=TransactionType.PURCHASE,
    description="Purchase",
    idempotency_key="unique_payment_id_123"  # Same key
)
# Raises DuplicateTransactionError
```

**Best Practices:**
- Use payment provider IDs as idempotency keys
- Generate UUID for internal operations
- Format: `{operation}_{user_id}_{uuid}`

## Usage Examples

### 1. User Purchases Credits

```python
# Frontend initiates
response = await client.post("/api/credits/purchase/initiate", json={
    "package_id": "popular",
    "payment_provider": "stripe"
})

client_secret = response.json()["client_secret"]

# Frontend uses Stripe.js to complete payment
# On success, confirm purchase

confirm = await client.post("/api/credits/purchase/confirm", json={
    "payment_id": "pi_abc123",
    "payment_provider": "stripe",
    "package_id": "popular"
})

print(confirm.json())
# {"success": true, "credits_added": 130, "new_balance": 130}
```

### 2. User Sends Paid Message

```python
# Check if creator requires payment
creator_profile = await Profile.find_one(Profile.user_id == creator_id)
cost = creator_profile.price_per_message  # e.g., 5 credits

# Spend credits
tx = await CreditsService.spend_credits(
    user_id=sender_id,
    amount=cost,
    transaction_type=TransactionType.MESSAGE,
    description=f"Message to {creator_profile.display_name}",
    idempotency_key=f"message_{message_id}",
    related_user_id=creator_id,
    related_entity_type="message",
    related_entity_id=message_id
)

# Add credits to creator
creator_tx = await CreditsService.add_credits(
    user_id=creator_id,
    amount=cost,
    transaction_type=TransactionType.BONUS,
    description=f"Message revenue from fan",
    related_user_id=sender_id
)
```

### 3. User Tips Creator

```python
# Frontend
response = await client.post("/api/credits/tip", json={
    "creator_id": "507f1f77bcf86cd799439011",
    "amount": 50,
    "message": "Amazing content!"
})

# System:
# 1. Deducts 50 credits from tipper
# 2. Adds 50 credits to creator
# 3. Both transactions linked
```

### 4. Admin Compensates User

```python
# Admin dashboard
response = await client.post("/api/credits/admin/adjust", 
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "user_id": "user_123",
        "amount": 100,
        "reason": "Compensation for downtime",
        "idempotency_key": "compensation_incident_456"
    }
)
```

### 5. Admin Refunds Purchase

```python
response = await client.post("/api/credits/admin/refund",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "transaction_id": "tx_purchase_123",
        "reason": "Disputed charge - customer request",
        "idempotency_key": "refund_dispute_789"
    }
)

# Original transaction marked as REVERSED
# New REFUND transaction created
# User balance updated
```

## Testing

Run comprehensive unit tests:

```bash
pytest backend/tests/test_credits.py -v
```

**Test Coverage:**
- ✅ Add credits (purchase, admin grant, bonus)
- ✅ Spend credits (message, tip, unlock)
- ✅ Refund credits
- ✅ Idempotency (duplicate prevention)
- ✅ Insufficient balance
- ✅ Concurrent operations (race conditions)
- ✅ Transaction history
- ✅ Balance queries

## Database Schema

### User Collection
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "credits_balance": 150,  // ← Current balance
  "..."
}
```

### Credits Transactions Collection (Ledger)
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "amount": -10,  // Negative = spent
  "transaction_type": "message",
  "status": "completed",
  "balance_before": 150,
  "balance_after": 140,
  "description": "Message to creator",
  "idempotency_key": "message_xyz_123",
  "related_user_id": ObjectId("creator_id"),
  "related_entity_type": "message",
  "related_entity_id": "msg_456",
  "created_at": ISODate("2025-12-05T10:30:00Z")
}
```

## Security Considerations

1. **ACID Transactions**: All operations use MongoDB transactions to prevent race conditions
2. **Idempotency**: Prevents double-charging from network retries
3. **Immutable Ledger**: Transactions cannot be deleted, only reversed
4. **Admin-Only Refunds**: Regular users cannot refund themselves
5. **Balance Validation**: Spending checks sufficient balance before deduction
6. **Audit Trail**: Every operation logged with user_id, amount, and metadata

## Error Handling

```python
from backend.services.credits_service import (
    InsufficientCreditsError,
    DuplicateTransactionError
)

try:
    tx = await CreditsService.spend_credits(...)
except InsufficientCreditsError as e:
    # User doesn't have enough credits
    return {"error": "insufficient_credits", "message": str(e)}
except DuplicateTransactionError:
    # Idempotency key already used
    return {"error": "duplicate_transaction"}
```

## Performance Optimization

1. **Indexes:**
   - `user_id + created_at` (transaction history)
   - `idempotency_key` (duplicate check)
   - `payment_id` (payment lookups)
   - `status + created_at` (pending transactions)

2. **Caching:**
   - Cache user balance in Redis for read-heavy workloads
   - Invalidate on transaction completion

3. **Batch Operations:**
   - For bulk rewards/penalties, use batch processing
   - Queue operations in Celery for async execution

## Migration Notes

If upgrading from old credit system:

```bash
# Run migration script
python backend/migrations/migrate_credits.py

# Verify balances match
python backend/migrations/verify_credit_balances.py
```

## Monitoring

**Key Metrics:**
- Total credits purchased (daily, monthly)
- Total credits spent by type
- Average transaction value
- Refund rate
- Failed transactions
- Idempotency collision rate

**Alerts:**
- High refund rate (> 5%)
- Balance reconciliation errors
- Transaction processing failures

## Support

**Common Issues:**

1. **"Insufficient credits" error**
   - User balance too low
   - Check transaction history for unexpected deductions
   - Admin can adjust balance if needed

2. **"Duplicate transaction" error**
   - Idempotency key already used
   - Check if transaction already completed
   - Generate new idempotency key for new transaction

3. **Purchase not reflecting**
   - Check payment webhook delivery
   - Verify idempotency key not reused
   - Admin can manually add credits with purchase proof

## Conclusion

The Pairly credits system provides:
- ✅ ACID-compliant transactions
- ✅ Idempotent operations
- ✅ Comprehensive audit trail
- ✅ Payment integration (Stripe, Razorpay)
- ✅ Admin management tools
- ✅ Full unit test coverage

The system is production-ready and scales to handle high transaction volumes with MongoDB's native transaction support.
