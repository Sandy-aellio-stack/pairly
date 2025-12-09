from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum
import hashlib
import json


class LedgerAccountType(str, Enum):
    """Ledger account types"""
    USER_CREDITS = "user_credits"  # User's credits account
    REVENUE = "revenue"  # Company revenue account
    REFUNDS = "refunds"  # Refunds account
    ADJUSTMENTS = "adjustments"  # Manual adjustments account
    SYSTEM = "system"  # System operations account


class LedgerEntryType(str, Enum):
    """Ledger entry types"""
    PAYMENT = "payment"  # Payment received
    REFUND = "refund"  # Refund issued
    CREDIT_ADD = "credit_add"  # Credits added
    CREDIT_DEDUCT = "credit_deduct"  # Credits deducted
    ADJUSTMENT = "adjustment"  # Manual adjustment


class FinancialLedgerEntry(Document):
    """
    Financial Ledger Entry - Double-entry accounting system.
    
    Immutable, append-only, hash-chained for tamper detection.
    
    Double-entry rules:
    - Every transaction has equal debits and credits
    - Debit = money going out of an account
    - Credit = money going into an account
    
    Example: User buys 100 credits for ₹100
    - Debit: revenue (₹100 out)
    - Credit: user_credits_<user_id> (100 credits in)
    """
    
    # Core fields
    id: str = Field(..., description="Ledger entry ID")
    sequence_number: int = Field(..., index=True, description="Sequential entry number")
    
    # Double-entry accounts
    debit_account: str = Field(..., description="Account being debited (money out)")
    credit_account: str = Field(..., description="Account being credited (money in)")
    
    # Amount
    amount: int = Field(..., ge=0, description="Amount in smallest unit (credits or cents)")
    currency: str = Field(default="credits", description="Currency type (credits, INR, USD)")
    
    # Entry metadata
    entry_type: LedgerEntryType = Field(...)
    description: str = Field(...)
    reference_id: str = Field(..., index=True, description="Reference to source transaction")
    reference_type: str = Field(..., description="Type of reference (payment_intent, refund, etc.)")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Hash chain for immutability
    entry_hash: str = Field(..., description="Hash of this entry")
    previous_hash: str = Field(..., description="Hash of previous entry")
    
    # Idempotency
    idempotency_key: str = Field(..., index=True, unique=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(default="system", description="User/system that created entry")
    
    # Immutability flag
    is_immutable: bool = Field(default=True)
    
    class Settings:
        name = "financial_ledger_entries"
        indexes = [
            "sequence_number",
            "debit_account",
            "credit_account",
            "reference_id",
            "idempotency_key",
            "entry_type",
            "created_at",
        ]
    
    def compute_hash(self) -> str:
        """
        Compute hash of this ledger entry.
        
        Includes: sequence_number, accounts, amount, reference, previous_hash
        """
        hash_data = {
            "sequence_number": self.sequence_number,
            "debit_account": self.debit_account,
            "credit_account": self.credit_account,
            "amount": self.amount,
            "currency": self.currency,
            "entry_type": self.entry_type,
            "reference_id": self.reference_id,
            "previous_hash": self.previous_hash,
            "created_at": self.created_at.isoformat()
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_hash(self) -> bool:
        """Verify that the stored hash matches computed hash"""
        return self.entry_hash == self.compute_hash()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "sequence_number": self.sequence_number,
            "debit_account": self.debit_account,
            "credit_account": self.credit_account,
            "amount": self.amount,
            "currency": self.currency,
            "entry_type": self.entry_type,
            "description": self.description,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "entry_hash": self.entry_hash,
            "previous_hash": self.previous_hash,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }


class LedgerBalance(BaseModel):
    """Ledger account balance"""
    account: str
    balance: int
    currency: str
    last_updated: datetime
