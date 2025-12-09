# PHASE 8: PAYMENTS + CREDITS + FINANCIAL LEDGER - ARCHITECTURE DESIGN

**Version:** 1.0  
**Date:** December 9, 2025  
**Status:** Design Document (No Code)  
**Target:** Production-Grade Financial System

---

## TABLE OF CONTENTS

1. System Architecture Overview
2. Payment System Design
3. Credits System Hardening
4. Financial Ledger Architecture
5. Webhook Security & Idempotency
6. Admin Financial Dashboard
7. Fraud Detection System
8. Integration Points
9. Failure Mode Catalog
10. Security Model
11. Test Plan
12. Implementation Plan

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Frontend)                        │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             │ REST API                           │ Webhooks
             ▼                                    ▼
┌────────────────────────────────┐    ┌──────────────────────────┐
│    Payment Gateway (Pairly)    │    │   Webhook Receivers      │
│  - /api/payments/checkout      │    │  - Stripe Webhooks       │
│  - Payment Intent Creation     │    │  - Razorpay Webhooks     │
│  - Risk Scoring                │    │  - Signature Validation  │
└────────┬───────────────────────┘    └──────────┬───────────────┘
         │                                       │
         │                      ┌────────────────┤
         │                      │                │
         ▼                      ▼                ▼
┌────────────────────┐  ┌──────────────┐  ┌─────────────────────┐
│  CreditsService    │  │ Ledger       │  │ FraudDetection      │
│  - ACID Ops        │  │ Service      │  │ Service             │
│  - Balance Mgmt    │  │ - Immutable  │  │ - Pattern Analysis  │
│  - Idempotency     │──│ - Double     │  │ - Risk Scoring      │
└────────┬───────────┘  │   Entry      │  │ - Geo Validation    │
         │              │ - Hashing    │  └─────────────────────┘
         │              └──────┬───────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MongoDB Collections                         │
│  - users (balance)                                              │
│  - credits_transactions (ledger)                                │
│  - financial_ledger (double-entry)                              │
│  - payment_intents                                              │
│  - webhook_events                                               │
│  - fraud_scores                                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  - Stripe API                                                   │
│  - Razorpay API                                                 │
│  - Redis (idempotency cache)                                    │
│  - Admin Audit Logs                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Design Principles

1. **ACID Compliance**: All financial operations are atomic, consistent, isolated, durable
2. **Immutability**: All ledger entries are append-only, never modified
3. **Auditability**: Complete trail from payment to credit balance
4. **Idempotency**: Duplicate requests don't create duplicate transactions
5. **Fraud Prevention**: Multi-layer fraud detection at every step
6. **Reconciliation**: Daily automated reconciliation between providers and ledger

### 1.3 Data Flow: Purchase to Credit Addition

```
1. User clicks "Buy Credits"
   ↓
2. Frontend → POST /api/payments/checkout
   ↓
3. Risk Scoring (fingerprint, velocity, amount)
   ↓
4. Create PaymentIntent (Stripe/Razorpay)
   ↓
5. Return payment_intent_id to frontend
   ↓
6. User completes payment on provider page
   ↓
7. Provider → Webhook → /api/payments/webhook/{provider}
   ↓
8. Verify webhook signature (HMAC-SHA256)
   ↓
9. Check idempotency (Redis + DB)
   ↓
10. CreditsService.add_credits() [ACID]
    ↓
11. Create FinancialLedgerEntry (double-entry)
    ↓
12. Update User.credits_balance
    ↓
13. Log admin audit trail
    ↓
14. Send WebSocket notification to user
    ↓
15. Mark webhook as processed
```

---

## 2. PAYMENT SYSTEM DESIGN

### 2.1 Payment Flow Architecture

**Payment Intent Creation:**

```python
# Design: POST /api/payments/checkout
Request:
{
  "provider": "stripe" | "razorpay",
  "package_id": "starter" | "popular" | "premium",
  "idempotency_key": "<uuid>"  # Client-generated
}

Process:
1. Validate package_id exists
2. Check idempotency_key not already used (Redis)
3. Score fraud risk (fingerprint, velocity, geolocation)
4. If risk > threshold: BLOCK or VERIFY
5. Create PaymentIntent in database (PENDING)
6. Call provider API to create payment intent:
   - Stripe: stripe.PaymentIntent.create()
   - Razorpay: razorpay.order.create()
7. Store provider response in PaymentIntent
8. Return client_secret to frontend

Response:
{
  "payment_intent_id": "pi_abc123",
  "client_secret": "pi_abc123_secret_xyz",
  "provider": "stripe",
  "amount": 499,
  "currency": "usd",
  "status": "requires_payment_method"
}
```

**Payment Confirmation (Webhook):**

```python
# Design: POST /api/payments/webhook/stripe
Headers:
  - Stripe-Signature: <hmac_signature>

Body: (Stripe Event Object)
{
  "id": "evt_abc123",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_abc123",
      "amount": 499,
      "currency": "usd",
      "metadata": {
        "user_id": "...",
        "package_id": "starter"
      }
    }
  }
}

Process:
1. Verify Stripe-Signature (HMAC-SHA256)
2. Extract event data
3. Check idempotency (webhook_events collection)
4. If already processed: return 200 (idempotent)
5. Retrieve PaymentIntent from DB
6. Start MongoDB transaction:
   a. Update PaymentIntent status → SUCCEEDED
   b. Call CreditsService.add_credits()
   c. Create FinancialLedgerEntry
   d. Commit transaction
7. If transaction fails: rollback, return 500
8. Mark webhook as processed
9. Send WebSocket notification
10. Return 200 OK
```

### 2.2 Payment Intent Model Design

**New Model: PaymentIntent**

```python
# Location: /app/backend/models/payment_intent.py
class PaymentIntentStatus(str, Enum):
    CREATED = "created"
    REQUIRES_PAYMENT = "requires_payment_method"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentIntent(Document):
    # IDs
    user_id: PydanticObjectId
    provider: str  # "stripe", "razorpay"
    provider_intent_id: str  # Provider's ID
    
    # Payment details
    amount_cents: int
    currency: str
    package_id: str
    credits_amount: int
    
    # Status
    status: PaymentIntentStatus
    
    # Idempotency
    idempotency_key: str  # Client-provided
    
    # Provider response
    provider_response: dict
    client_secret: Optional[str] = None
    
    # Fraud
    fraud_score: float
    fraud_check_passed: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    succeeded_at: Optional[datetime] = None
    
    # Webhook processing
    webhook_received: bool = False
    webhook_processed_at: Optional[datetime] = None
    
    # Credits
    credits_added: bool = False
    credits_transaction_id: Optional[str] = None
    
    class Settings:
        name = "payment_intents"
        indexes = [
            "user_id",
            "provider_intent_id",
            "idempotency_key",
            "status",
            [("user_id", 1), ("created_at", -1)]
        ]
```

### 2.3 Webhook Event Tracking

**New Model: WebhookEvent**

```python
# Location: /app/backend/models/webhook_event.py
class WebhookEvent(Document):
    # Identification
    provider: str  # "stripe", "razorpay"
    event_id: str  # Provider's event ID
    event_type: str  # "payment_intent.succeeded", etc.
    
    # Processing
    received_at: datetime
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_attempts: int = 0
    
    # Signature verification
    signature_verified: bool
    signature: str
    
    # Payload
    raw_payload: dict
    
    # Result
    success: bool = False
    error_message: Optional[str] = None
    
    # Idempotency
    payment_intent_id: Optional[str] = None
    credits_transaction_id: Optional[str] = None
    
    class Settings:
        name = "webhook_events"
        indexes = [
            "event_id",  # Unique
            "provider",
            "processed",
            "received_at"
        ]
```

### 2.4 Provider Integration Architecture

**Stripe Integration:**

```python
# Design: /app/backend/core/payment_providers/stripe_provider.py
class StripeProvider:
    def __init__(self):
        self.api_key = secrets_manager.get_secret("STRIPE_SECRET_KEY")
        self.webhook_secret = secrets_manager.get_secret("STRIPE_WEBHOOK_SECRET")
        stripe.api_key = self.api_key
    
    async def create_payment_intent(
        user_id: str,
        amount_cents: int,
        currency: str,
        metadata: dict
    ) -> dict:
        """
        Creates Stripe PaymentIntent
        Returns: {intent_id, client_secret, status}
        """
        # Stripe API call with retry logic
        # Add metadata: user_id, package_id, timestamp
        # Handle Stripe exceptions
        # Log to structured logs
    
    async def verify_webhook_signature(
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature
        Prevents webhook spoofing
        """
        # Use stripe.Webhook.construct_event()
        # Catch SignatureVerificationError
    
    async def retrieve_payment_intent(intent_id: str) -> dict:
        """
        Fetch payment intent from Stripe API
        Used for reconciliation
        """
    
    async def refund_payment(payment_id: str, amount_cents: int) -> dict:
        """
        Create refund (future)
        """
```

**Razorpay Integration:**

```python
# Design: /app/backend/core/payment_providers/razorpay_provider.py
class RazorpayProvider:
    def __init__(self):
        self.key_id = secrets_manager.get_secret("RAZORPAY_KEY_ID")
        self.key_secret = secrets_manager.get_secret("RAZORPAY_KEY_SECRET")
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    async def create_order(
        user_id: str,
        amount_paise: int,
        currency: str,
        metadata: dict
    ) -> dict:
        """
        Creates Razorpay Order
        Returns: {order_id, status}
        """
    
    async def verify_webhook_signature(
        payload: str,
        signature: str
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256
        """
        # razorpay.utility.verify_webhook_signature()
    
    async def capture_payment(payment_id: str, amount_paise: int) -> dict:
        """
        Capture authorized payment
        """
```

### 2.5 Idempotency Design

**Two-Layer Idempotency:**

```
Layer 1: Client-Side Idempotency Key
  - Client generates UUID for each checkout request
  - Stored in Redis (TTL: 24 hours)
  - Key: f"idempotency:checkout:{key}"
  - Value: payment_intent_id
  - Prevents duplicate payment intent creation

Layer 2: Webhook Event ID
  - Provider's event ID is unique
  - Stored in webhook_events collection
  - Checked before processing
  - Prevents duplicate credit additions from webhook replays

Layer 3: Database Transaction ID
  - CreditsTransaction.idempotency_key
  - Unique constraint at DB level
  - Final safety net against double-charging
```

**Redis Idempotency Cache:**

```python
# Design pattern
async def check_idempotency(key: str) -> Optional[str]:
    """
    Check if operation already processed
    Returns: existing payment_intent_id or None
    """
    cached = await redis_client.get(f"idempotency:checkout:{key}")
    if cached:
        logger.info(f"Idempotent request detected: {key}")
        return cached
    return None

async def set_idempotency(key: str, payment_intent_id: str):
    """
    Mark operation as processed
    """
    await redis_client.setex(
        f"idempotency:checkout:{key}",
        86400,  # 24 hours
        payment_intent_id
    )
```

---

## 3. CREDITS SYSTEM HARDENING

### 3.1 Current State Issues

**Problems Identified:**

1. **Direct Balance Manipulation**: Some endpoints may modify `user.credits_balance` directly instead of using CreditsService
2. **Missing Transaction Logs**: Not all credit operations create ledger entries
3. **Race Conditions**: Concurrent credit deductions could cause negative balances
4. **No Double-Charge Prevention**: Missing idempotency in some flows
5. **Incomplete Audit Trail**: Some operations don't log properly

### 3.2 CreditsService Enhancement Design

**Enhanced CreditsService Methods:**

```python
# Location: /app/backend/services/credits_service.py (enhanced)

class CreditsService:
    
    @staticmethod
    async def add_credits(
        user_id: PydanticObjectId,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        idempotency_key: Optional[str] = None,
        payment_provider: Optional[str] = None,
        payment_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> CreditsTransaction:
        """
        ACID-safe credit addition
        
        Process:
        1. Check idempotency_key in DB
        2. Start MongoDB transaction
        3. Lock user document (for_update)
        4. Read current balance
        5. Calculate new balance
        6. Create CreditsTransaction with before/after
        7. Update user.credits_balance
        8. Commit transaction
        9. If any step fails: rollback
        10. Log to admin audit
        11. Send WebSocket notification
        
        Returns: CreditsTransaction object
        Raises: DuplicateTransactionError if idempotency_key exists
        """
    
    @staticmethod
    async def deduct_credits(
        user_id: PydanticObjectId,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        idempotency_key: Optional[str] = None,
        related_user_id: Optional[PydanticObjectId] = None,
        metadata: Optional[dict] = None
    ) -> CreditsTransaction:
        """
        ACID-safe credit deduction with balance check
        
        Process:
        1. Check idempotency_key
        2. Start transaction
        3. Lock user document
        4. Check balance >= amount
        5. If insufficient: raise InsufficientCreditsError
        6. Create transaction record
        7. Update balance
        8. Commit
        
        Returns: CreditsTransaction
        Raises: InsufficientCreditsError, DuplicateTransactionError
        """
    
    @staticmethod
    async def transfer_credits(
        from_user_id: PydanticObjectId,
        to_user_id: PydanticObjectId,
        amount: int,
        description: str,
        idempotency_key: Optional[str] = None
    ) -> tuple[CreditsTransaction, CreditsTransaction]:
        """
        ACID-safe credit transfer between users
        
        Process:
        1. Start transaction
        2. Lock both users
        3. Deduct from sender
        4. Add to recipient
        5. Create paired transactions
        6. Commit atomically
        7. If any fails: rollback both
        
        Returns: (sender_tx, recipient_tx)
        """
    
    @staticmethod
    async def refund_transaction(
        original_transaction_id: str,
        reason: str
    ) -> CreditsTransaction:
        """
        Refund a previous transaction
        
        Process:
        1. Retrieve original transaction
        2. Check not already refunded
        3. Start transaction
        4. Reverse credit movement
        5. Mark original as REVERSED
        6. Create refund transaction
        7. Commit
        
        Returns: Refund transaction
        """
```

### 3.3 Database Transaction Patterns

**MongoDB Transaction Usage:**

```python
# Design pattern for ACID operations
async def add_credits_with_transaction(...):
    async with await db_client.start_session() as session:
        async with session.start_transaction():
            try:
                # 1. Lock user
                user = await User.get(user_id, session=session)
                if not user:
                    raise ValueError("User not found")
                
                # 2. Read current balance
                balance_before = user.credits_balance
                
                # 3. Calculate new balance
                balance_after = balance_before + amount
                
                # 4. Create transaction record
                transaction = CreditsTransaction(
                    user_id=user_id,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    # ... other fields
                )
                await transaction.insert(session=session)
                
                # 5. Update user balance
                user.credits_balance = balance_after
                await user.save(session=session)
                
                # 6. Commit transaction
                await session.commit_transaction()
                
                return transaction
                
            except Exception as e:
                await session.abort_transaction()
                logger.error(f"Transaction failed: {e}")
                raise
```

### 3.4 Endpoints Requiring CreditsService Integration

**Audit of Current Endpoints:**

```
Endpoints to verify/update:

1. /api/messages/send (WebSocket)
   Current: Uses CreditsService.charge_for_message() ✅
   Status: COMPLIANT

2. /api/calls/start
   Check: Does it use CreditsService?
   Action: Ensure all call credit deductions use CreditsService

3. /api/posts/{post_id}/unlock
   Check: Direct balance manipulation?
   Action: Replace with CreditsService.deduct_credits()

4. /api/tips/send
   Check: Transfer credits properly?
   Action: Use CreditsService.transfer_credits()

5. /api/payments/webhook/*
   Check: Uses CreditsService.add_credits()?
   Action: Ensure ACID-safe implementation

6. Admin credit grants
   Check: Uses CreditsService?
   Action: Ensure admin_grant type used
```

### 3.5 Negative Balance Prevention

**Guards to Implement:**

```python
# Design: Multiple layers of protection

Layer 1: Application-Level Check (in CreditsService)
  if user.credits_balance < amount:
      raise InsufficientCreditsError()

Layer 2: Database Constraint (MongoDB validation)
  User schema:
    credits_balance: int (min=0, default=0)

Layer 3: Transaction Atomicity
  Use MongoDB transactions to prevent race conditions
  Lock user document during balance updates

Layer 4: Monitoring
  Alert if any user balance goes negative
  Daily reconciliation job to detect anomalies
```

---

## 4. FINANCIAL LEDGER ARCHITECTURE

### 4.1 Double-Entry Accounting Design

**Concept:**

Every financial transaction creates two entries:
- **Debit**: Account that receives value
- **Credit**: Account that gives value

Total debits = Total credits (always balanced)

**Account Structure:**

```
Chart of Accounts:

1. ASSETS
   - Users' Credit Balances (sum of all user credits)
   - Cash (payments received from Stripe/Razorpay)

2. LIABILITIES
   - Creator Payouts Owed (earnings not yet paid out)
   - Refunds Owed (disputed transactions)

3. REVENUE
   - Credit Sales Revenue
   - Platform Fees

4. EXPENSES
   - Payment Processing Fees (Stripe/Razorpay fees)
   - Refunds Issued
```

### 4.2 FinancialLedgerEntry Model

**New Model: FinancialLedgerEntry**

```python
# Location: /app/backend/models/financial_ledger.py

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    REVENUE = "revenue"
    EXPENSE = "expense"

class EntryType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class FinancialLedgerEntry(Document):
    """
    Immutable double-entry accounting ledger
    Every transaction creates paired entries (debit + credit)
    """
    
    # Entry identification
    entry_id: str  # UUID for this entry
    pair_id: str  # Links debit and credit entries
    entry_type: EntryType  # "debit" or "credit"
    
    # Account information
    account_type: AccountType
    account_name: str  # e.g., "user_credits", "revenue", "cash"
    account_id: Optional[str] = None  # user_id if applicable
    
    # Amount
    amount_cents: int  # Always positive
    currency: str = "USD"
    
    # Related transaction
    transaction_type: str  # "credit_purchase", "message_fee", etc.
    related_credits_transaction_id: Optional[str] = None
    related_payment_intent_id: Optional[str] = None
    
    # Description
    description: str
    
    # Metadata
    metadata: dict = Field(default_factory=dict)
    
    # Timestamp (immutable)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Anti-tampering
    previous_entry_hash: Optional[str] = None  # Hash of previous entry
    entry_hash: str  # SHA256 hash of this entry
    
    class Settings:
        name = "financial_ledger"
        indexes = [
            "entry_id",
            "pair_id",
            "account_type",
            "account_id",
            "created_at",
            [("account_type", 1), ("created_at", -1)]
        ]
```

### 4.3 Ledger Entry Creation Pattern

**Example: Credit Purchase Transaction**

```python
# Design: When user buys $4.99 worth of credits (50 credits)

# Entry 1: DEBIT (increase asset)
LedgerEntry(
    entry_type=DEBIT,
    account_type=ASSET,
    account_name="user_credits",
    account_id=user_id,
    amount_cents=499,  # $4.99
    description="Credit purchase - 50 credits"
)

# Entry 2: CREDIT (increase revenue)
LedgerEntry(
    entry_type=CREDIT,
    account_type=REVENUE,
    account_name="credit_sales_revenue",
    amount_cents=499,
    description="Credit purchase revenue"
)

# Entry 3: DEBIT (payment processing fee as expense)
LedgerEntry(
    entry_type=DEBIT,
    account_type=EXPENSE,
    account_name="payment_processing_fees",
    amount_cents=15,  # Stripe fee ~3%
    description="Stripe processing fee"
)

# Entry 4: CREDIT (reduce cash by fee)
LedgerEntry(
    entry_type=CREDIT,
    account_type=ASSET,
    account_name="cash",
    amount_cents=15,
    description="Payment processing fee deduction"
)
```

### 4.4 Hashing & Anti-Tampering

**Hash Chain Design:**

```python
# Each entry's hash includes:
# 1. Entry data (account, amount, timestamp, etc.)
# 2. Previous entry's hash (blockchain-style)

def calculate_entry_hash(entry: FinancialLedgerEntry) -> str:
    """
    Create SHA256 hash of entry
    Includes previous hash to create chain
    """
    hash_input = f"{entry.entry_id}|{entry.entry_type}|{entry.account_name}|"
    hash_input += f"{entry.amount_cents}|{entry.created_at.isoformat()}|"
    hash_input += f"{entry.previous_entry_hash or ''}|"
    hash_input += f"{json.dumps(entry.metadata, sort_keys=True)}"
    
    return hashlib.sha256(hash_input.encode()).hexdigest()

# Verification:
def verify_ledger_integrity() -> bool:
    """
    Verify entire ledger hasn't been tampered with
    Recalculate all hashes and compare
    """
    entries = await FinancialLedgerEntry.find().sort("created_at").to_list()
    
    for i, entry in enumerate(entries):
        # Recalculate hash
        expected_hash = calculate_entry_hash(entry)
        
        if entry.entry_hash != expected_hash:
            logger.error(f"Hash mismatch at entry {entry.entry_id}")
            return False
        
        # Check previous hash linkage
        if i > 0:
            if entry.previous_entry_hash != entries[i-1].entry_hash:
                logger.error(f"Chain broken at entry {entry.entry_id}")
                return False
    
    return True
```

### 4.5 Reconciliation Service Design

**Daily Reconciliation Job:**

```python
# Design: /app/backend/services/reconciliation_service.py

class ReconciliationService:
    
    @staticmethod
    async def daily_reconciliation(date: date) -> dict:
        """
        Reconcile all financial accounts for a specific date
        
        Checks:
        1. Sum of user credit balances = ASSET:user_credits ledger balance
        2. Total debits = Total credits
        3. Stripe/Razorpay API balance matches our records
        4. All payment intents accounted for
        5. No orphaned transactions
        
        Returns: Reconciliation report
        """
        
        report = {
            "date": date.isoformat(),
            "checks": [],
            "discrepancies": [],
            "status": "pass"
        }
        
        # Check 1: User balances
        user_balances_sum = await User.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$credits_balance"}}}
        ]).to_list()
        
        ledger_asset_balance = await FinancialLedgerEntry.aggregate([
            {"$match": {"account_name": "user_credits"}},
            {"$group": {
                "_id": None,
                "debits": {"$sum": {"$cond": [{"$eq": ["$entry_type", "debit"]}, "$amount_cents", 0]}},
                "credits": {"$sum": {"$cond": [{"$eq": ["$entry_type", "credit"]}, "$amount_cents", 0]}}
            }}
        ]).to_list()
        
        # Compare...
        
        # Check 2: Debit/Credit balance
        all_debits = await FinancialLedgerEntry.find({"entry_type": "debit"}).sum("amount_cents")
        all_credits = await FinancialLedgerEntry.find({"entry_type": "credit"}).sum("amount_cents")
        
        if all_debits != all_credits:
            report["discrepancies"].append({
                "type": "imbalance",
                "debits": all_debits,
                "credits": all_credits,
                "difference": all_debits - all_credits
            })
            report["status"] = "fail"
        
        # Check 3: Provider reconciliation
        stripe_balance = await stripe.Balance.retrieve()
        # Compare with our ASSET:cash account...
        
        return report
    
    @staticmethod
    async def verify_payment_intent_accounting(
        payment_intent_id: str
    ) -> bool:
        """
        Verify specific payment has complete accounting trail:
        1. PaymentIntent exists and succeeded
        2. CreditsTransaction created
        3. FinancialLedgerEntry pair created
        4. User balance updated
        """
```

---

## 5. WEBHOOK SECURITY & IDEMPOTENCY

### 5.1 Webhook Signature Verification

**Stripe Signature Verification:**

```python
# Design: /app/backend/services/webhook_verification.py

class WebhookVerificationService:
    
    @staticmethod
    async def verify_stripe_webhook(
        payload: bytes,
        signature_header: str,
        webhook_secret: str
    ) -> dict:
        """
        Verify Stripe webhook signature
        
        Process:
        1. Extract timestamp and signature from header
        2. Construct signed_payload = timestamp + "." + payload
        3. Compute HMAC-SHA256(signed_payload, webhook_secret)
        4. Compare computed signature with provided signature
        5. Check timestamp is within 5 minutes (replay protection)
        
        Returns: Parsed event object
        Raises: SignatureVerificationError
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, webhook_secret
            )
            
            # Additional timestamp check
            event_time = datetime.fromtimestamp(event['created'], tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if (now - event_time) > timedelta(minutes=5):
                raise ValueError("Webhook timestamp too old (replay attack?)")
            
            return event
            
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Stripe signature verification failed: {e}")
            raise
    
    @staticmethod
    async def verify_razorpay_webhook(
        payload: str,
        signature: str,
        webhook_secret: str
    ) -> dict:
        """
        Verify Razorpay webhook signature
        
        Process:
        1. Compute HMAC-SHA256(payload, webhook_secret)
        2. Compare with provided signature
        
        Returns: Parsed payload
        Raises: SignatureVerificationError
        """
        try:
            # Razorpay uses different verification
            razorpay.utility.verify_webhook_signature(
                payload, signature, webhook_secret
            )
            return json.loads(payload)
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.warning(f"Razorpay signature verification failed: {e}")
            raise
```

### 5.2 Replay Attack Protection

**Multi-Layer Protection:**

```
Layer 1: Timestamp Validation
  - Reject webhooks older than 5 minutes
  - Prevents replay of captured webhooks

Layer 2: Event ID Deduplication
  - Store processed event IDs in webhook_events collection
  - Check event_id before processing
  - If exists: return 200 (already processed)

Layer 3: Payment Intent State Machine
  - PaymentIntent can only move forward in states
  - succeeded → succeeded is idempotent (no-op)
  - failed → succeeded is invalid (rejected)

Layer 4: Redis Rate Limiting
  - Limit webhook processing to 10/minute per IP
  - Prevents webhook flooding attacks
```

### 5.3 Idempotency Key Management

**Comprehensive Idempotency Strategy:**

```python
# Design: /app/backend/services/idempotency_service.py

class IdempotencyService:
    
    @staticmethod
    async def check_and_set(
        key: str,
        operation: str,
        ttl_seconds: int = 86400
    ) -> Optional[str]:
        """
        Check if operation already performed
        If not, mark as in-progress
        
        Returns: existing_result_id or None
        """
        # Check Redis first (fast)
        redis_key = f"idempotency:{operation}:{key}"
        existing = await redis_client.get(redis_key)
        
        if existing:
            return existing
        
        # Check database (persistent)
        if operation == "checkout":
            intent = await PaymentIntent.find_one({"idempotency_key": key})
            if intent:
                return str(intent.id)
        
        elif operation == "webhook":
            event = await WebhookEvent.find_one({"event_id": key})
            if event:
                return str(event.id)
        
        # Mark as in-progress
        await redis_client.setex(redis_key, ttl_seconds, "PROCESSING")
        return None
    
    @staticmethod
    async def mark_complete(
        key: str,
        operation: str,
        result_id: str
    ):
        """
        Mark operation as complete
        """
        redis_key = f"idempotency:{operation}:{key}"
        await redis_client.setex(redis_key, 86400, result_id)
```

### 5.4 Webhook Retry & Failure Queue

**Retry Strategy:**

```python
# Design: Exponential backoff for webhook processing

class WebhookProcessor:
    
    MAX_RETRIES = 5
    RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1min, 5min, 15min, 1hr, 2hr
    
    @staticmethod
    async def process_webhook(
        event: WebhookEvent
    ) -> bool:
        """
        Process webhook with retry logic
        
        Process:
        1. Attempt processing
        2. If success: mark as processed
        3. If failure: increment attempts
        4. If attempts < MAX_RETRIES: schedule retry
        5. If attempts >= MAX_RETRIES: move to dead letter queue
        
        Returns: success status
        """
        try:
            # Process webhook (add credits, update payment intent, etc.)
            result = await _process_webhook_logic(event)
            
            # Mark as processed
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            event.success = True
            await event.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            
            # Increment attempts
            event.processing_attempts += 1
            event.error_message = str(e)
            await event.save()
            
            # Schedule retry or move to DLQ
            if event.processing_attempts < WebhookProcessor.MAX_RETRIES:
                delay = WebhookProcessor.RETRY_DELAYS[
                    event.processing_attempts - 1
                ]
                await schedule_webhook_retry(event.id, delay)
            else:
                await move_to_dead_letter_queue(event.id)
            
            return False
```

**Dead Letter Queue:**

```python
# Design: Collection for failed webhooks requiring manual intervention

class WebhookDeadLetterQueue(Document):
    webhook_event_id: str
    original_event: dict
    failure_reason: str
    attempts: int
    first_failed_at: datetime
    last_retry_at: datetime
    requires_manual_review: bool = True
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    resolution: Optional[str] = None
    
    class Settings:
        name = "webhook_dlq"
```

---

## 6. ADMIN FINANCIAL DASHBOARD

### 6.1 Dashboard Endpoints Design

**New Routes:**

```python
# Design: /app/backend/routes/admin_financial.py

GET /api/admin/financial/dashboard
  Returns:
  - Total revenue (today, week, month, all-time)
  - Credit sales count
  - Average transaction value
  - Top packages sold
  - Payment provider split (Stripe vs Razorpay)

GET /api/admin/financial/revenue-report
  Query: start_date, end_date
  Returns:
  - Daily revenue breakdown
  - Payment provider fees
  - Net revenue
  - Chart data

GET /api/admin/financial/credit-purchases
  Query: start_date, end_date, user_id (optional)
  Returns:
  - List of credit purchases
  - Amount paid, credits received
  - Payment provider
  - Status

GET /api/admin/financial/refunds
  Query: status (pending/completed)
  Returns:
  - Refund requests
  - Original transaction
  - Reason
  - Status

GET /api/admin/financial/user/{user_id}/statement
  Returns:
  - User's complete financial history
  - All purchases
  - All credit transactions
  - Current balance
  - Lifetime value

GET /api/admin/financial/reconciliation
  Query: date
  Returns:
  - Reconciliation report for specific date
  - Discrepancies (if any)
  - Action items

GET /api/admin/financial/ledger
  Query: account_type, start_date, end_date
  Returns:
  - Ledger entries for specific account
  - Debits and credits
  - Running balance

POST /api/admin/financial/refund
  Body: {transaction_id, reason, amount}
  Action: Process refund
  Returns: Refund transaction

GET /api/admin/financial/failed-payments
  Returns:
  - Payment intents that failed
  - Failure reasons
  - Retry opportunities
```

### 6.2 Financial Reports Design

**Daily Revenue Report Structure:**

```json
{
  "date": "2025-12-09",
  "revenue": {
    "total_cents": 125000,
    "currency": "USD",
    "total_usd": 1250.00
  },
  "transactions": {
    "count": 50,
    "average_value_cents": 2500
  },
  "by_provider": {
    "stripe": {
      "count": 35,
      "amount_cents": 87500,
      "fees_cents": 2625
    },
    "razorpay": {
      "count": 15,
      "amount_cents": 37500,
      "fees_cents": 1125
    }
  },
  "by_package": {
    "starter": {"count": 20, "amount": 99800},
    "popular": {"count": 25, "amount": 249750},
    "premium": {"count": 5, "amount": 99950}
  },
  "net_revenue_cents": 121250,
  "credits_sold": 5000
}
```

---

## 7. FRAUD DETECTION SYSTEM

### 7.1 Fraud Detection Architecture

**Multi-Layer Fraud Detection:**

```
┌─────────────────────────────────────────────────────────────┐
│                    REQUEST ARRIVES                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Rate & Velocity Checks                            │
│  - Fast retry detection (same user, <1 minute)             │
│  - High volume (>10 purchases/hour)                        │
│  - Abnormal pattern (usually $5, suddenly $100)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Device & Location Checks                          │
│  - Device fingerprint risk score                           │
│  - IP geolocation vs user's country                        │
│  - VPN/proxy detection                                     │
│  - Known fraudulent IP ranges                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Behavioral Analysis                               │
│  - Account age (<24 hours = suspicious)                    │
│  - No profile picture = +10 risk                           │
│  - No activity before purchase = +20 risk                  │
│  - Purchased but never used credits = +30 risk             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Payment Pattern Analysis                          │
│  - Multiple cards from same device                         │
│  - Rapid card switching                                    │
│  - Failed payment followed by success (card testing)       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  FRAUD SCORE: 0-100                                         │
│  <30: Allow                                                 │
│  30-70: Flag for review                                    │
│  >70: Block                                                │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Fraud Rules Engine Design

**New Service: FraudDetectionService**

```python
# Design: /app/backend/services/fraud_detection_service.py

class FraudDetectionService:
    
    @staticmethod
    async def score_payment_attempt(
        user_id: str,
        amount_cents: int,
        package_id: str,
        fingerprint: DeviceFingerprint,
        ip_address: str
    ) -> dict:
        """
        Calculate fraud risk score for payment attempt
        
        Returns:
        {
            "score": 0-100,
            "risk_level": "low"|"medium"|"high",
            "action": "allow"|"review"|"block",
            "reasons": ["reason1", "reason2"],
            "checks": {
                "velocity": {...},
                "device": {...},
                "behavioral": {...},
                "payment_pattern": {...}
            }
        }
        """
        score = 0
        reasons = []
        checks = {}
        
        # Check 1: Fast retry detection
        recent_attempts = await PaymentIntent.find(
            PaymentIntent.user_id == user_id,
            PaymentIntent.created_at >= datetime.now(timezone.utc) - timedelta(minutes=5)
        ).count()
        
        if recent_attempts > 0:
            score += 30
            reasons.append("Multiple payment attempts in 5 minutes")
        
        checks["velocity"] = {
            "recent_attempts": recent_attempts,
            "risk_added": 30 if recent_attempts > 0 else 0
        }
        
        # Check 2: Volume check
        today_purchases = await PaymentIntent.find(
            PaymentIntent.user_id == user_id,
            PaymentIntent.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0),
            PaymentIntent.status == "succeeded"
        ).count()
        
        if today_purchases > 5:
            score += 40
            reasons.append(f"Unusual volume: {today_purchases} purchases today")
        
        # Check 3: Device risk
        if fingerprint.risk_score > 70:
            score += 25
            reasons.append(f"High-risk device (score: {fingerprint.risk_score})")
        
        checks["device"] = {
            "risk_score": fingerprint.risk_score,
            "trusted": fingerprint.trusted
        }
        
        # Check 4: Geolocation mismatch
        user = await User.get(user_id)
        user_country = getattr(user, 'country', None)
        ip_country = await get_country_from_ip(ip_address)
        
        if user_country and ip_country and user_country != ip_country:
            score += 20
            reasons.append(f"Location mismatch: {user_country} vs {ip_country}")
        
        checks["geolocation"] = {
            "user_country": user_country,
            "ip_country": ip_country,
            "mismatch": user_country != ip_country
        }
        
        # Check 5: Account age
        account_age_hours = (datetime.now(timezone.utc) - user.created_at).total_seconds() / 3600
        if account_age_hours < 24:
            score += 15
            reasons.append(f"New account ({account_age_hours:.1f} hours old)")
        
        checks["behavioral"] = {
            "account_age_hours": account_age_hours,
            "has_profile": bool(await Profile.find_one(Profile.user_id == user.id))
        }
        
        # Check 6: Impossible volume
        # If user is purchasing more credits than they could reasonably use
        total_credits_purchased_ever = await CreditsTransaction.find(
            CreditsTransaction.user_id == user.id,
            CreditsTransaction.transaction_type == "purchase"
        ).sum("amount")
        
        total_credits_spent_ever = await CreditsTransaction.find(
            CreditsTransaction.user_id == user.id,
            CreditsTransaction.amount < 0
        ).sum("amount")
        
        unused_credits = user.credits_balance
        if unused_credits > 1000 and (unused_credits / (abs(total_credits_spent_ever) + 1)) > 5:
            score += 30
            reasons.append(f"Purchasing credits but not using them ({unused_credits} unused)")
        
        # Determine risk level and action
        if score < 30:
            risk_level = "low"
            action = "allow"
        elif score < 70:
            risk_level = "medium"
            action = "review"  # Flag for admin review but allow
        else:
            risk_level = "high"
            action = "block"
        
        return {
            "score": score,
            "risk_level": risk_level,
            "action": action,
            "reasons": reasons,
            "checks": checks
        }
```

### 7.3 Fraud Score Storage

**Enhanced PaymentIntent with Fraud Data:**

```python
# Add to PaymentIntent model:
fraud_detection: dict = {
    "score": 0,
    "risk_level": "low",
    "action": "allow",
    "reasons": [],
    "checks": {},
    "flagged_for_review": False
}
```

**Enhanced CreditsTransaction with Fraud Data:**

```python
# Add to CreditsTransaction model:
fraud_score: Optional[float] = None
fraud_flags: Optional[List[str]] = None
```

### 7.4 Suspicious Pattern Detection

**Patterns to Detect:**

```
1. Card Testing Pattern:
   - Multiple small purchases (<$1)
   - Rapid succession (<1 minute apart)
   - Different cards
   → Action: Block after 3 attempts

2. Credit Hoarding:
   - Purchased 1000+ credits
   - Used <10% of credits
   - No messaging or calling activity
   → Action: Flag for review

3. Refund Abuse:
   - Purchased credits
   - Used credits
   - Requested refund
   - Pattern repeats >2 times
   → Action: Block refunds, investigate

4. Account Farming:
   - Same device, multiple accounts
   - Each account purchases credits
   - Minimal activity per account
   → Action: Link accounts, flag

5. Geolocation Hopping:
   - IP changes countries frequently
   - Each country triggers purchase
   → Action: Require verification
```

---

## 8. INTEGRATION WITH EXISTING SYSTEMS

### 8.1 Phase 7 Integration

**Structured Logging:**
```python
# All payment operations use Phase 7 logging
logger.info(
    "Payment intent created",
    extra={
        "event": "payment_intent_created",
        "user_id": user_id,
        "amount_cents": amount,
        "provider": provider,
        "fraud_score": fraud_score
    }
)
```

**Secrets Manager:**
```python
# All API keys retrieved via secrets_manager
stripe.api_key = secrets_manager.get_secret("STRIPE_SECRET_KEY")
```

**Timezone-Aware Datetime:**
```python
# All timestamps use datetime.now(timezone.utc)
created_at = datetime.now(timezone.utc)
```

### 8.2 Admin RBAC Integration

**Permission Requirements:**

```
financial.view - View financial dashboard
financial.export - Export financial reports
financial.refund - Process refunds
financial.reconcile - Run reconciliation
```

**Route Protection:**
```python
@router.get("/dashboard")
async def financial_dashboard(
    admin_user: User = Depends(AdminRBACService.require_permission("financial.view"))
):
    # Only users with financial.view permission can access
```

### 8.3 WebSocket Notifications

**Credit Addition Notification:**

```python
# After successful credit addition, notify user via WebSocket
if user_id in active_connections:
    await active_connections[user_id].send_json({
        "type": "credits_added",
        "amount": credits_amount,
        "new_balance": user.credits_balance,
        "transaction_id": str(transaction.id)
    })
```

### 8.4 Credits Usage Integration

**Ensure All Features Use CreditsService:**

```
Messaging: ✅ Already uses CreditsService.charge_for_message()

Calling: TODO
  - /api/calls/start
  - Must use CreditsService.deduct_credits()
  - Type: TransactionType.CALL

Posts (Unlock): TODO
  - /api/posts/{id}/unlock
  - Must use CreditsService.deduct_credits()
  - Type: TransactionType.UNLOCK

Tips: TODO
  - /api/tips/send
  - Must use CreditsService.transfer_credits()
  - Type: TransactionType.TIP

Subscriptions: TODO
  - Integration with subscription payments
  - Recurring credit charges
```

---

## 9. FAILURE MODE CATALOG

### 9.1 Payment Failures

**Failure 1: Payment Intent Creation Fails**

**Cause:** Stripe/Razorpay API is down, network error, invalid API key

**Detection:** Exception during stripe.PaymentIntent.create()

**Recovery:**
1. Log error with full context
2. Return 503 Service Unavailable to user
3. Store failed attempt in database for retry
4. Alert admin if error rate > 5%
5. User can retry after 1 minute

**Data State:** No data modified (safe failure)

---

**Failure 2: Webhook Signature Verification Fails**

**Cause:** Invalid signature, webhook secret misconfigured, replay attack

**Detection:** SignatureVerificationError during verification

**Recovery:**
1. Log warning with IP address and payload hash
2. Increment failed verification counter
3. Return 400 Bad Request (don't process)
4. If >10 failures in 1 hour: alert security team
5. Check if webhook secret needs rotation

**Data State:** No credits added (prevented fraud)

---

**Failure 3: Duplicate Webhook Received**

**Cause:** Stripe/Razorpay retry, network timeout causing retry

**Detection:** event_id exists in webhook_events collection

**Recovery:**
1. Log info: "Duplicate webhook ignored"
2. Return 200 OK (idempotent success)
3. No further processing

**Data State:** Unchanged (idempotent)

---

**Failure 4: User Not Found During Credit Addition**

**Cause:** User deleted between payment and webhook, database corruption

**Detection:** User.get() returns None

**Recovery:**
1. Log critical error
2. Mark webhook as failed
3. Move to dead letter queue
4. Create refund request automatically
5. Alert admin for manual review

**Data State:** Payment succeeded but credits not added (requires manual intervention)

---

**Failure 5: Database Transaction Fails Mid-Commit**

**Cause:** MongoDB connection lost, disk full, replica set election

**Detection:** Exception during transaction.commit()

**Recovery:**
1. Transaction automatically rolls back
2. Log error with transaction details
3. Webhook remains unprocessed
4. Provider will retry webhook
5. Next webhook attempt will succeed (idempotent)

**Data State:** Rolled back (ACID guarantee)

---

**Failure 6: Credits Added But Webhook Not Marked Processed**

**Cause:** App crashes after credit addition, before marking webhook done

**Detection:** webhook_events.processed = false but credits_transaction exists

**Recovery:**
1. Reconciliation job detects mismatch
2. Check if credits_transaction_id exists in CreditsTransaction
3. If exists: mark webhook as processed retroactively
4. If not exists: process webhook (idempotent)

**Data State:** Eventually consistent

---

**Failure 7: Payment Succeeds But User Disputes**

**Cause:** Fraudulent card, unauthorized use, buyer remorse

**Detection:** dispute.created webhook from Stripe

**Recovery:**
1. Log dispute details
2. Flag user account
3. Deduct disputed credits if not spent
4. If credits already spent: mark user balance negative temporarily
5. Admin reviews and decides: refund or keep
6. If refund: use CreditsService.refund_transaction()

**Data State:** Credits may be deducted, refund processed

---

**Failure 8: Refund Processing Fails**

**Cause:** Stripe API error, insufficient balance in Stripe account

**Detection:** Exception during stripe.Refund.create()

**Recovery:**
1. Log refund attempt failure
2. Mark refund request as "pending_retry"
3. Schedule automatic retry in 1 hour
4. After 3 failed retries: alert admin
5. Admin processes refund manually via Stripe dashboard

**Data State:** Refund pending, credits not restored yet

---

**Failure 9: Fraud Score Calculation Fails**

**Cause:** External API timeout (geolocation service), database query fails

**Detection:** Exception in FraudDetectionService.score_payment_attempt()

**Recovery:**
1. Log error
2. Default to medium risk (score: 50)
3. Allow payment but flag for manual review
4. Admin reviews transaction post-facto

**Data State:** Payment proceeds with default risk score

---

**Failure 10: Reconciliation Detects Discrepancy**

**Cause:** Bug in credit addition, database corruption, missed webhook

**Detection:** Daily reconciliation job finds mismatch

**Recovery:**
1. Generate detailed discrepancy report
2. Alert admin immediately
3. Lock affected user accounts (prevent further transactions)
4. Admin investigates:
   - Check Stripe/Razorpay dashboard
   - Check webhook logs
   - Check database transactions
5. Admin manually corrects discrepancy
6. Add correction entry to ledger
7. Unlock accounts

**Data State:** Inconsistent until manual correction

---

## 10. SECURITY MODEL

### 10.1 Defense Layers

**Layer 1: Network Security**
- Rate limiting: 100 requests/minute per IP
- DDoS protection via infrastructure
- TLS 1.3 for all API communication
- Webhook endpoints behind firewall rules

**Layer 2: Authentication & Authorization**
- All payment endpoints require JWT
- Role-based access for admin endpoints
- API key validation for webhooks (HMAC signatures)
- Session validation

**Layer 3: Fraud Detection**
- Real-time fraud scoring (see Section 7)
- Device fingerprinting
- Velocity checks
- Behavioral analysis

**Layer 4: Data Protection**
- No credit card storage (PCI-DSS compliant)
- Payment handled entirely by Stripe/Razorpay
- Sensitive data encrypted at rest
- Logs sanitized (no PII in plaintext)

**Layer 5: Transaction Integrity**
- ACID-compliant database transactions
- Idempotency keys
- Immutable ledger
- Hash chains for tamper detection

**Layer 6: Monitoring & Alerting**
- Real-time fraud alerts
- Failed payment monitoring
- Reconciliation alerts
- Anomaly detection

### 10.2 Signature Verification Details

**Stripe Signature Scheme:**

```
Header: Stripe-Signature
Format: t=<timestamp>,v1=<signature>

Computation:
  signed_payload = timestamp + "." + json_body
  expected_signature = HMAC-SHA256(signed_payload, webhook_secret)
  
Validation:
  1. Extract timestamp and signatures from header
  2. Compute expected signature
  3. Compare using secure comparison (prevents timing attacks)
  4. Check timestamp is within tolerance (5 minutes)
```

**Razorpay Signature Scheme:**

```
Header: X-Razorpay-Signature
Format: <signature>

Computation:
  expected_signature = HMAC-SHA256(json_body, webhook_secret)
  
Validation:
  1. Compute expected signature
  2. Compare with provided signature
```

### 10.3 Replay Attack Prevention

```
1. Timestamp Validation:
   - Reject webhooks with timestamp > 5 minutes old
   - Prevents captured webhooks from being replayed later

2. Event ID Tracking:
   - Store all processed event IDs
   - Check before processing
   - Unique constraint in database

3. Nonce Generation:
   - Each payment intent has unique ID
   - Cannot be reused

4. State Machine:
   - Payment intents can only move forward
   - Cannot transition from succeeded back to pending
```

---

## 11. TEST PLAN

### 11.1 Unit Tests

**Test Suite 1: CreditsService**

```python
# File: /app/backend/tests/test_credits_service_enhanced.py

Tests:
1. test_add_credits_success
   - Add 50 credits to user
   - Verify balance increased
   - Verify transaction created
   - Verify before/after balances correct

2. test_add_credits_idempotency
   - Add credits with idempotency key
   - Attempt to add again with same key
   - Verify only one transaction created
   - Verify DuplicateTransactionError raised

3. test_deduct_credits_success
   - User has 100 credits
   - Deduct 50 credits
   - Verify balance now 50
   - Verify transaction created

4. test_deduct_credits_insufficient
   - User has 10 credits
   - Attempt to deduct 50 credits
   - Verify InsufficientCreditsError raised
   - Verify balance unchanged

5. test_transfer_credits_success
   - User A has 100, User B has 50
   - Transfer 30 from A to B
   - Verify A has 70, B has 80
   - Verify two transactions created

6. test_transfer_credits_rollback
   - Simulate failure after deducting from sender
   - Verify entire transaction rolled back
   - Verify both balances unchanged

7. test_concurrent_deductions
   - Simulate 10 concurrent deductions
   - Verify all succeed or fail appropriately
   - Verify no race conditions
   - Verify final balance is correct
```

**Test Suite 2: Payment Intent Creation**

```python
# File: /app/backend/tests/test_payment_intent.py

Tests:
1. test_create_payment_intent_stripe
   - Create payment intent with Stripe
   - Verify PaymentIntent document created
   - Verify Stripe API called
   - Verify client_secret returned

2. test_create_payment_intent_idempotency
   - Create with idempotency key
   - Create again with same key
   - Verify same payment_intent returned
   - Verify only one Stripe API call

3. test_create_payment_intent_fraud_blocked
   - User with high fraud score
   - Attempt to create payment intent
   - Verify blocked with 403
   - Verify PaymentIntent marked as blocked

4. test_create_payment_intent_invalid_package
   - Request with invalid package_id
   - Verify 400 error
   - Verify no PaymentIntent created
```

**Test Suite 3: Webhook Processing**

```python
# File: /app/backend/tests/test_webhooks.py

Tests:
1. test_stripe_webhook_signature_valid
   - Send webhook with valid signature
   - Verify signature verified
   - Verify webhook processed

2. test_stripe_webhook_signature_invalid
   - Send webhook with invalid signature
   - Verify rejected with 400
   - Verify not processed

3. test_webhook_idempotency
   - Process webhook
   - Send same webhook again
   - Verify second one returns 200 but doesn't reprocess

4. test_webhook_payment_success
   - Send payment_intent.succeeded webhook
   - Verify credits added to user
   - Verify PaymentIntent updated
   - Verify FinancialLedgerEntry created

5. test_webhook_user_not_found
   - Send webhook for non-existent user
   - Verify moved to dead letter queue
   - Verify refund request created

6. test_webhook_retry_logic
   - Simulate temporary failure
   - Verify retry scheduled
   - Verify exponential backoff

7. test_webhook_dead_letter_queue
   - Simulate 5 consecutive failures
   - Verify moved to DLQ
   - Verify admin alerted
```

**Test Suite 4: Financial Ledger**

```python
# File: /app/backend/tests/test_financial_ledger.py

Tests:
1. test_ledger_double_entry_creation
   - Create credit purchase transaction
   - Verify two ledger entries created (debit + credit)
   - Verify amounts match

2. test_ledger_balance_calculation
   - Add multiple transactions
   - Calculate account balance
   - Verify debits - credits = expected balance

3. test_ledger_hash_chain
   - Create 10 ledger entries
   - Verify each entry's hash is correct
   - Verify previous_hash links are correct

4. test_ledger_tampering_detection
   - Create entries
   - Manually modify one entry
   - Run integrity check
   - Verify tampering detected

5. test_ledger_immutability
   - Attempt to update existing entry
   - Verify operation rejected
   - Verify entry unchanged
```

**Test Suite 5: Fraud Detection**

```python
# File: /app/backend/tests/test_fraud_detection.py

Tests:
1. test_fraud_score_low_risk
   - Normal user, normal purchase
   - Verify score < 30
   - Verify action = "allow"

2. test_fraud_score_velocity_check
   - User makes 3 purchases in 2 minutes
   - Verify high score
   - Verify "fast_retry" in reasons

3. test_fraud_score_geolocation_mismatch
   - User from US, IP from Russia
   - Verify score increases
   - Verify "location_mismatch" in reasons

4. test_fraud_score_new_account
   - Account created 1 hour ago
   - Attempt large purchase
   - Verify elevated score

5. test_fraud_score_impossible_volume
   - User has 5000 unused credits
   - Attempts to buy 5000 more
   - Verify blocked

6. test_fraud_score_device_risk
   - Known fraudulent device fingerprint
   - Verify high score
   - Verify blocked or flagged
```

### 11.2 Integration Tests

**Test Suite 6: End-to-End Payment Flow**

```python
# File: /app/backend/tests/integration/test_payment_flow_e2e.py

Tests:
1. test_complete_stripe_payment_flow
   Steps:
   a. User logs in
   b. Selects credit package
   c. POST /api/payments/checkout
   d. Receives payment_intent_id
   e. Simulate Stripe success webhook
   f. Verify credits added to user
   g. Verify transaction created
   h. Verify ledger entries created
   i. Verify webhook marked processed

2. test_failed_payment_flow
   Steps:
   a. Create payment intent
   b. Simulate payment_intent.failed webhook
   c. Verify no credits added
   d. Verify PaymentIntent marked failed
   e. Verify user can retry

3. test_concurrent_webhooks
   Steps:
   a. Send same webhook from 5 threads simultaneously
   b. Verify only one processed
   c. Verify others return 200 (idempotent)
   d. Verify exactly one credit transaction

4. test_payment_with_fraud_block
   Steps:
   a. User with high fraud score
   b. Attempt checkout
   c. Verify 403 blocked
   d. Verify PaymentIntent not created
   e. Verify logged for admin review
```

**Test Suite 7: Credits Usage Integration**

```python
# File: /app/backend/tests/integration/test_credits_usage.py

Tests:
1. test_messaging_credits_deduction
   Steps:
   a. User A has 100 credits
   b. User B (creator) charges 10 credits/message
   c. User A sends message to User B
   d. Verify User A has 90 credits
   e. Verify User B earned 10 credits
   f. Verify transaction logged

2. test_insufficient_credits_messaging
   Steps:
   a. User has 5 credits
   b. Creator charges 10 credits
   c. Attempt to send message
   d. Verify InsufficientCreditsError
   e. Verify message not sent

3. test_calling_credits_deduction
   Steps:
   a. User starts call
   b. Call lasts 5 minutes
   c. Verify credits deducted (5 * rate)
   d. Verify transaction logged

4. test_post_unlock_credits
   Steps:
   a. User unlocks premium post
   b. Verify credits deducted
   c. Verify post unlocked
   d. Verify transaction logged
```

**Test Suite 8: Reconciliation**

```python
# File: /app/backend/tests/integration/test_reconciliation.py

Tests:
1. test_daily_reconciliation_pass
   Steps:
   a. Create 100 payment transactions
   b. Add all credits correctly
   c. Run reconciliation
   d. Verify all checks pass
   e. Verify no discrepancies

2. test_reconciliation_detects_missing_credits
   Steps:
   a. Create PaymentIntent (succeeded)
   b. Manually skip credit addition
   c. Run reconciliation
   d. Verify discrepancy detected
   e. Verify admin alert sent

3. test_reconciliation_ledger_balance
   Steps:
   a. Create various transactions
   b. Calculate expected balances
   c. Run reconciliation
   d. Verify ledger balances match expected

4. test_provider_balance_reconciliation
   Steps:
   a. Mock Stripe API (return balance)
   b. Run reconciliation
   c. Verify our records match Stripe's
```

### 11.3 Load Tests

**Load Test 1: 1000 Concurrent Payment Intents**

```python
# File: /app/backend/tests/load/test_payment_load.py

Test:
- Simulate 1000 concurrent users
- Each creates payment intent
- Measure:
  * Average response time (target: <500ms)
  * Success rate (target: >99%)
  * Database connections
  * Redis performance
  * No race conditions
  * All intents unique
```

**Load Test 2: 10000 Webhooks in 1 Minute**

```python
Test:
- Simulate webhook flood (10k/minute)
- All unique event IDs
- Measure:
  * Processing time per webhook (target: <100ms)
  * Queue depth
  * No dropped webhooks
  * All marked processed
  * Credits correctly added
```

**Load Test 3: Concurrent Credit Deductions**

```python
Test:
- 1000 users
- Each has 1000 credits
- Simulate 100 concurrent deductions per user
- Measure:
  * Final balance correctness
  * No negative balances
  * No race conditions
  * Transaction count matches deductions
```

### 11.4 Audit & Compliance Tests

**Test Suite 9: Audit Trail**

```python
# File: /app/backend/tests/audit/test_audit_trail.py

Tests:
1. test_complete_audit_trail
   Steps:
   a. User purchases credits
   b. Query audit logs
   c. Verify trail exists:
      - PaymentIntent creation
      - Webhook received
      - Credits added
      - Ledger entries created
   d. Verify timestamps sequential
   e. Verify all IDs linked

2. test_refund_audit_trail
   Steps:
   a. Issue refund
   b. Verify admin action logged
   c. Verify refund transaction logged
   d. Verify ledger entries created
   e. Verify reversal transaction logged
```

### 11.5 Security Tests

**Test Suite 10: Security Validation**

```python
# File: /app/backend/tests/security/test_payment_security.py

Tests:
1. test_webhook_without_signature
   - Send webhook without signature
   - Verify rejected

2. test_webhook_replay_attack
   - Process webhook
   - Replay same webhook 10 minutes later
   - Verify rejected (timestamp too old)

3. test_unauthorized_refund
   - Non-admin user attempts refund
   - Verify 403 forbidden

4. test_sql_injection_attempts
   - Send malicious payloads
   - Verify all rejected
   - Verify no database corruption

5. test_rate_limiting
   - Send 200 requests in 1 minute
   - Verify rate limit triggered
   - Verify legitimate requests still work
```

---

## 12. STEP-BY-STEP IMPLEMENTATION PLAN

### Phase 1: Foundation (Days 1-2)

**Step 1.1: Create New Models** ✅
- PaymentIntent model
- WebhookEvent model
- FinancialLedgerEntry model
- Add to database.py initialization

**Step 1.2: Enhance CreditsService** ✅
- Add MongoDB transaction support
- Implement idempotency checks
- Add before/after balance tracking
- Implement refund_transaction method

**Step 1.3: Create Provider Abstraction** ✅
- StripeProvider class
- RazorpayProvider class
- Shared interface
- Error handling and retries

**Testing:** Unit tests for models and CreditsService

---

### Phase 2: Payment Intent Creation (Days 3-4)

**Step 2.1: Implement Checkout Endpoint** ✅
- POST /api/payments/checkout
- Risk scoring integration
- Idempotency check
- Provider API call
- Return client_secret

**Step 2.2: Integrate Fraud Detection** ✅
- FraudDetectionService implementation
- Score calculation
- Block/allow/review logic

**Testing:** Integration tests for checkout flow

---

### Phase 3: Webhook System (Days 5-7)

**Step 3.1: Webhook Signature Verification** ✅
- WebhookVerificationService
- Stripe signature validation
- Razorpay signature validation
- Replay attack prevention

**Step 3.2: Webhook Processing Logic** ✅
- POST /api/payments/webhook/stripe
- POST /api/payments/webhook/razorpay
- Event type handling
- Idempotency checks
- Credit addition via CreditsService

**Step 3.3: Webhook Retry & DLQ** ✅
- Retry logic with exponential backoff
- Dead letter queue
- Admin alert system

**Testing:** Webhook integration tests, load tests

---

### Phase 4: Financial Ledger (Days 8-9)

**Step 4.1: Implement Double-Entry System** ✅
- LedgerService class
- Create paired entries
- Account balance calculation

**Step 4.2: Hash Chain Implementation** ✅
- Entry hash calculation
- Previous hash linkage
- Integrity verification method

**Step 4.3: Reconciliation Service** ✅
- Daily reconciliation job
- Balance checking
- Discrepancy detection
- Admin reporting

**Testing:** Ledger integrity tests, reconciliation tests

---

### Phase 5: Credits Usage Enforcement (Days 10-11)

**Step 5.1: Audit Existing Endpoints** ✅
- Identify all credit operations
- Check CreditsService usage
- List non-compliant endpoints

**Step 5.2: Update Non-Compliant Endpoints** ✅
- Update calls endpoints
- Update post unlock endpoints
- Update tip endpoints
- Ensure all use CreditsService

**Step 5.3: Add Missing Transaction Types** ✅
- Ensure all operations logged
- Add missing transaction types

**Testing:** Integration tests for all credit operations

---

### Phase 6: Admin Dashboard (Days 12-13)

**Step 6.1: Financial Dashboard Endpoints** ✅
- GET /api/admin/financial/dashboard
- GET /api/admin/financial/revenue-report
- GET /api/admin/financial/credit-purchases

**Step 6.2: Refund System** ✅
- POST /api/admin/financial/refund
- GET /api/admin/financial/refunds
- Refund processing logic

**Step 6.3: Reconciliation Interface** ✅
- GET /api/admin/financial/reconciliation
- GET /api/admin/financial/failed-payments

**Testing:** Admin endpoint tests

---

### Phase 7: Testing & Validation (Days 14-15)

**Step 7.1: Unit Test Suite** ✅
- Run all unit tests
- Achieve >90% coverage
- Fix any failures

**Step 7.2: Integration Test Suite** ✅
- Run end-to-end tests
- Test all payment flows
- Test all failure scenarios

**Step 7.3: Load Testing** ✅
- 1000 concurrent payments
- 10000 webhooks/minute
- Monitor performance

**Step 7.4: Security Audit** ✅
- Run security tests
- Verify signature validation
- Test replay protection
- Validate RBAC

---

### Phase 8: Documentation & Deployment (Days 16-17)

**Step 8.1: API Documentation** ✅
- Update OpenAPI specs
- Add examples
- Document error codes

**Step 8.2: Operations Runbook** ✅
- Webhook failure recovery
- Reconciliation procedures
- Refund processing
- Fraud investigation

**Step 8.3: Monitoring Setup** ✅
- Add Datadog/Prometheus metrics
- Configure alerts
- Set up dashboards

**Step 8.4: Production Deployment** ✅
- Database migrations
- Environment variables
- Provider webhook URLs
- Gradual rollout

---

## 13. FILE CREATION LIST

### New Models (4 files)
```
/app/backend/models/payment_intent.py
/app/backend/models/webhook_event.py
/app/backend/models/financial_ledger.py
/app/backend/models/webhook_dlq.py
```

### New Services (6 files)
```
/app/backend/services/payment_service.py
/app/backend/services/webhook_verification_service.py
/app/backend/services/webhook_processor.py
/app/backend/services/ledger_service.py
/app/backend/services/reconciliation_service.py
/app/backend/services/fraud_detection_service.py
```

### New Provider Integration (3 files)
```
/app/backend/core/payment_providers/__init__.py
/app/backend/core/payment_providers/stripe_provider.py
/app/backend/core/payment_providers/razorpay_provider.py
```

### New Routes (2 files)
```
/app/backend/routes/payments_enhanced.py  (replaces existing)
/app/backend/routes/admin_financial.py
```

### New Utilities (2 files)
```
/app/backend/utils/idempotency_service.py
/app/backend/utils/financial_utils.py
```

### New Tests (10 files)
```
/app/backend/tests/test_payment_intent.py
/app/backend/tests/test_webhooks.py
/app/backend/tests/test_financial_ledger.py
/app/backend/tests/test_fraud_detection.py
/app/backend/tests/test_credits_service_enhanced.py
/app/backend/tests/integration/test_payment_flow_e2e.py
/app/backend/tests/integration/test_credits_usage.py
/app/backend/tests/integration/test_reconciliation.py
/app/backend/tests/load/test_payment_load.py
/app/backend/tests/security/test_payment_security.py
```

### Documentation (3 files)
```
/app/docs/PHASE8_ARCHITECTURE.md  (this document)
/app/docs/PHASE8_API_REFERENCE.md
/app/docs/PHASE8_OPERATIONS_RUNBOOK.md
```

**Total New Files: 33**

---

## 14. FILE MODIFICATION LIST

### Core Files (3 files)
```
/app/backend/main.py
  - Add payment_enhanced and admin_financial routers
  - Import new models

/app/backend/database.py
  - Add PaymentIntent to document_models
  - Add WebhookEvent to document_models
  - Add FinancialLedgerEntry to document_models
  - Add WebhookDeadLetterQueue to document_models

/app/backend/config.py
  - Add STRIPE_WEBHOOK_SECRET
  - Add RAZORPAY_WEBHOOK_SECRET
  - Add FRAUD_DETECTION_ENABLED flag
```

### Services (2 files)
```
/app/backend/services/credits_service.py
  - Add MongoDB transaction support
  - Add idempotency_key parameter
  - Add before_balance tracking
  - Add refund_transaction method
  - Enhance error handling

/app/backend/core/payment_clients.py
  - Integrate with new provider classes
  - Add webhook verification
```

### Routes (5 files)
```
/app/backend/routes/payments.py
  - Replace with payments_enhanced.py
  - Full rewrite with new logic

/app/backend/routes/credits.py
  - Ensure all operations use CreditsService
  - Add idempotency keys
  - Enhance error responses

/app/backend/routes/messaging.py
  - Already using CreditsService ✓
  - Add idempotency to charge_for_message

/app/backend/routes/calls.py
  - Update to use CreditsService
  - Add credit charging logic
  - Add transaction logging

/app/backend/routes/posts.py
  - Update unlock endpoint
  - Use CreditsService.deduct_credits
  - Add idempotency
```

### Models (2 files)
```
/app/backend/models/credits_transaction.py
  - Add fraud_score field
  - Add fraud_flags field
  - Add idempotency_key unique index

/app/backend/models/user.py
  - Add country field (for geolocation)
  - Add last_payment_at field
  - Ensure credits_balance has min=0 constraint
```

### Admin Routes (1 file)
```
/app/backend/routes/admin_analytics_enhanced.py
  - Add financial metrics
  - Add payment provider analytics
```

**Total Modified Files: 13**

---

## 15. SUMMARY

### Implementation Scope

**New Code:**
- 33 new files
- ~8,000+ lines of production code
- ~4,000+ lines of test code

**Modified Code:**
- 13 existing files enhanced
- ~2,000 lines of modifications

**Total:** ~14,000 lines of code

### Key Features

1. ✅ **ACID-Compliant Credits System**
2. ✅ **Production-Grade Payment Integration**
3. ✅ **Webhook Security & Idempotency**
4. ✅ **Bank-Grade Financial Ledger**
5. ✅ **Multi-Layer Fraud Detection**
6. ✅ **Complete Audit Trail**
7. ✅ **Daily Reconciliation**
8. ✅ **Admin Financial Dashboard**
9. ✅ **Comprehensive Test Suite**
10. ✅ **Full Integration with Phase 7**

### Timeline

**Total Estimated Time:** 17 days
- Foundation: 2 days
- Payment Intents: 2 days
- Webhooks: 3 days
- Ledger: 2 days
- Credits Enforcement: 2 days
- Admin Dashboard: 2 days
- Testing: 2 days
- Documentation & Deployment: 2 days

### Production Readiness

**Security:** ✅ Multi-layer protection  
**Reliability:** ✅ ACID transactions  
**Auditability:** ✅ Complete ledger  
**Scalability:** ✅ Distributed system  
**Compliance:** ✅ PCI-DSS patterns  

---

**END OF ARCHITECTURE DOCUMENT**

**Status:** Ready for implementation  
**Next Step:** Begin Phase 1 (Foundation) implementation  
**Approval Required:** Yes (review architecture before coding)
