import logging
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from backend.models.financial_ledger import (
    FinancialLedgerEntry,
    LedgerAccountType,
    LedgerEntryType,
    LedgerBalance
)

logger = logging.getLogger('service.ledger')


class LedgerService:
    """
    Financial Ledger Service - Double-entry accounting system.
    
    Features:
    - Append-only ledger
    - Hash-chained entries (blockchain-style)
    - Idempotency support
    - Balance calculation
    - Tamper detection
    """
    
    def __init__(self):
        self.genesis_hash = "0" * 64  # Genesis block hash
    
    async def record_entry(
        self,
        debit_account: str,
        credit_account: str,
        amount: int,
        currency: str,
        entry_type: LedgerEntryType,
        description: str,
        reference_id: str,
        reference_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        created_by: str = "system"
    ) -> FinancialLedgerEntry:
        """
        Record a double-entry ledger entry.
        
        Args:
            debit_account: Account being debited
            credit_account: Account being credited
            amount: Amount in smallest unit
            currency: Currency type
            entry_type: Type of entry
            description: Human-readable description
            reference_id: ID of source transaction
            reference_type: Type of source
            metadata: Additional data
            idempotency_key: Prevent duplicates
            created_by: User/system creating entry
        
        Returns:
            Created ledger entry
        
        Raises:
            ValueError: If validation fails
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            idempotency_key = f"{entry_type}_{reference_id}"
        
        # Check idempotency
        existing_entry = await FinancialLedgerEntry.find_one(
            FinancialLedgerEntry.idempotency_key == idempotency_key
        )
        
        if existing_entry:
            logger.info(
                f"Duplicate ledger entry detected",
                extra={
                    "idempotency_key": idempotency_key,
                    "existing_entry_id": existing_entry.id
                }
            )
            return existing_entry
        
        # Get next sequence number and previous hash
        sequence_number = await self._get_next_sequence_number()
        previous_hash = await self._get_latest_hash()
        
        # Create ledger entry
        entry = FinancialLedgerEntry(
            id=f"ledger_{secrets.token_hex(16)}",
            sequence_number=sequence_number,
            debit_account=debit_account,
            credit_account=credit_account,
            amount=amount,
            currency=currency,
            entry_type=entry_type,
            description=description,
            reference_id=reference_id,
            reference_type=reference_type,
            metadata=metadata or {},
            previous_hash=previous_hash,
            idempotency_key=idempotency_key,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            entry_hash=""  # Will be computed
        )
        
        # Compute and set hash
        entry.entry_hash = entry.compute_hash()
        
        # Save to database
        await entry.insert()
        
        logger.info(
            "Ledger entry recorded",
            extra={
                "event": "ledger_entry_created",
                "entry_id": entry.id,
                "sequence_number": sequence_number,
                "debit_account": debit_account,
                "credit_account": credit_account,
                "amount": amount,
                "currency": currency,
                "entry_type": entry_type,
                "reference_id": reference_id
            }
        )
        
        return entry
    
    async def record_payment(
        self,
        payment_intent_id: str,
        user_id: str,
        amount_cents: int,
        credits_amount: int,
        provider: str
    ) -> FinancialLedgerEntry:
        """
        Record a payment in the ledger.
        
        Double-entry:
        - Debit: revenue (money received)
        - Credit: user_credits (credits given)
        """
        return await self.record_entry(
            debit_account="revenue",
            credit_account=f"user_credits_{user_id}",
            amount=credits_amount,
            currency="credits",
            entry_type=LedgerEntryType.PAYMENT,
            description=f"Payment {payment_intent_id} via {provider} - \u20b9{amount_cents/100:.2f}",
            reference_id=payment_intent_id,
            reference_type="payment_intent",
            metadata={
                "user_id": user_id,
                "amount_cents": amount_cents,
                "credits_amount": credits_amount,
                "provider": provider
            },
            idempotency_key=f"payment_{payment_intent_id}"
        )
    
    async def record_refund(
        self,
        payment_intent_id: str,
        user_id: str,
        credits_amount: int
    ) -> FinancialLedgerEntry:
        """
        Record a refund in the ledger.
        
        Double-entry:
        - Debit: user_credits (credits taken back)
        - Credit: refunds (money refunded)
        """
        return await self.record_entry(
            debit_account=f"user_credits_{user_id}",
            credit_account="refunds",
            amount=credits_amount,
            currency="credits",
            entry_type=LedgerEntryType.REFUND,
            description=f"Refund for payment {payment_intent_id}",
            reference_id=payment_intent_id,
            reference_type="refund",
            metadata={
                "user_id": user_id,
                "credits_amount": credits_amount
            },
            idempotency_key=f"refund_{payment_intent_id}"
        )
    
    async def record_credit_deduction(
        self,
        transaction_id: str,
        user_id: str,
        amount: int,
        reason: str
    ) -> FinancialLedgerEntry:
        """
        Record a credit deduction (user spending credits).
        
        Double-entry:
        - Debit: user_credits (credits spent)
        - Credit: system (credits consumed)
        """
        return await self.record_entry(
            debit_account=f"user_credits_{user_id}",
            credit_account="system",
            amount=amount,
            currency="credits",
            entry_type=LedgerEntryType.CREDIT_DEDUCT,
            description=reason,
            reference_id=transaction_id,
            reference_type="credits_transaction",
            metadata={
                "user_id": user_id,
                "amount": amount
            },
            idempotency_key=f"deduct_{transaction_id}"
        )
    
    async def verify_chain_integrity(
        self,
        start_sequence: int = 0,
        end_sequence: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Verify ledger chain integrity.
        
        Checks:
        1. Each entry's hash is correct
        2. Each entry's previous_hash matches previous entry's hash
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get entries in sequence order
        query = FinancialLedgerEntry.sequence_number >= start_sequence
        if end_sequence:
            query = query & (FinancialLedgerEntry.sequence_number <= end_sequence)
        
        entries = await FinancialLedgerEntry.find(query).sort("sequence_number").to_list()
        
        if not entries:
            return True, None
        
        # Verify first entry
        if not entries[0].verify_hash():
            return False, f"Hash mismatch at sequence {entries[0].sequence_number}"
        
        # Verify chain
        for i in range(1, len(entries)):
            current = entries[i]
            previous = entries[i - 1]
            
            # Check hash
            if not current.verify_hash():
                return False, f"Hash mismatch at sequence {current.sequence_number}"
            
            # Check chain
            if current.previous_hash != previous.entry_hash:
                return False, f"Chain broken at sequence {current.sequence_number}"
        
        logger.info(
            f"Ledger chain verified",
            extra={
                "entries_checked": len(entries),
                "start_sequence": start_sequence,
                "end_sequence": end_sequence or "latest"
            }
        )
        
        return True, None
    
    async def get_account_balance(self, account: str) -> LedgerBalance:
        """
        Calculate account balance from ledger entries.
        
        Balance = Credits - Debits
        """
        # Get all entries for this account
        credit_entries = await FinancialLedgerEntry.find(
            FinancialLedgerEntry.credit_account == account
        ).to_list()
        
        debit_entries = await FinancialLedgerEntry.find(
            FinancialLedgerEntry.debit_account == account
        ).to_list()
        
        # Calculate balance
        credits = sum(entry.amount for entry in credit_entries)
        debits = sum(entry.amount for entry in debit_entries)
        balance = credits - debits
        
        # Get currency (assume all entries have same currency)
        currency = credit_entries[0].currency if credit_entries else "credits"
        
        # Get last update time
        all_entries = credit_entries + debit_entries
        last_updated = max((entry.created_at for entry in all_entries), default=datetime.now(timezone.utc))
        
        return LedgerBalance(
            account=account,
            balance=balance,
            currency=currency,
            last_updated=last_updated
        )
    
    async def get_entries_by_reference(
        self,
        reference_id: str,
        reference_type: Optional[str] = None
    ) -> List[FinancialLedgerEntry]:
        """Get all ledger entries for a specific reference"""
        query = FinancialLedgerEntry.reference_id == reference_id
        if reference_type:
            query = query & (FinancialLedgerEntry.reference_type == reference_type)
        
        return await FinancialLedgerEntry.find(query).sort("created_at").to_list()
    
    async def _get_next_sequence_number(self) -> int:
        """Get next sequence number for ledger entry"""
        latest_entry = await FinancialLedgerEntry.find_all().sort("-sequence_number").first_or_none()
        return (latest_entry.sequence_number + 1) if latest_entry else 1
    
    async def _get_latest_hash(self) -> str:
        """Get hash of latest ledger entry (for chain)"""
        latest_entry = await FinancialLedgerEntry.find_all().sort("-sequence_number").first_or_none()
        return latest_entry.entry_hash if latest_entry else self.genesis_hash


# Global instance
_ledger_service: Optional[LedgerService] = None


def get_ledger_service() -> LedgerService:
    """Get global ledger service instance"""
    global _ledger_service
    if _ledger_service is None:
        _ledger_service = LedgerService()
    return _ledger_service
