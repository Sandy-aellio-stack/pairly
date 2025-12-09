import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus
from backend.models.credits_transaction import CreditsTransaction
from backend.models.financial_ledger import FinancialLedgerEntry
from backend.models.user import User

logger = logging.getLogger('service.reconciliation')

class ReconciliationReport:
    def __init__(self):
        self.total_payments = 0
        self.total_ledger_debits = 0
        self.total_ledger_credits = 0
        self.discrepancies = []
        self.generated_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        return {
            "total_payments": self.total_payments,
            "total_ledger_debits": self.total_ledger_debits,
            "total_ledger_credits": self.total_ledger_credits,
            "discrepancies": self.discrepancies,
            "generated_at": self.generated_at.isoformat(),
            "status": "clean" if not self.discrepancies else "issues_found"
        }

class ReconciliationService:
    async def reconcile_payments_vs_ledger(self) -> ReconciliationReport:
        report = ReconciliationReport()
        
        # Get all successful payments
        payments = await PaymentIntent.find(
            PaymentIntent.status == PaymentIntentStatus.SUCCEEDED
        ).to_list()
        
        report.total_payments = len(payments)
        
        # Check each payment has ledger entry
        for payment in payments:
            ledger_entries = await FinancialLedgerEntry.find(
                FinancialLedgerEntry.reference_id == payment.id
            ).to_list()
            
            if not ledger_entries:
                report.discrepancies.append({
                    "type": "missing_ledger_entry",
                    "payment_id": payment.id,
                    "amount": payment.credits_amount
                })
        
        # Get ledger totals
        revenue_entries = await FinancialLedgerEntry.find(
            FinancialLedgerEntry.debit_account == "revenue"
        ).to_list()
        
        report.total_ledger_debits = sum(e.amount for e in revenue_entries)
        
        logger.info(f"Reconciliation complete: {len(report.discrepancies)} discrepancies found")
        return report
    
    async def reconcile_credits_vs_ledger(self, user_id: str) -> Dict[str, Any]:
        # Get user's actual credits balance
        user = await User.get(user_id)
        if not user:
            return {"error": "User not found"}
        
        actual_balance = user.credits_balance
        
        # Calculate from ledger
        credit_entries = await FinancialLedgerEntry.find(
            FinancialLedgerEntry.credit_account == f"user_credits_{user_id}"
        ).to_list()
        
        debit_entries = await FinancialLedgerEntry.find(
            FinancialLedgerEntry.debit_account == f"user_credits_{user_id}"
        ).to_list()
        
        ledger_balance = sum(e.amount for e in credit_entries) - sum(e.amount for e in debit_entries)
        
        discrepancy = actual_balance - ledger_balance
        
        return {
            "user_id": user_id,
            "actual_balance": actual_balance,
            "ledger_balance": ledger_balance,
            "discrepancy": discrepancy,
            "reconciled": discrepancy == 0
        }
    
    async def find_discrepancies(self) -> List[Dict[str, Any]]:
        discrepancies = []
        
        # Check payments without ledger entries
        payments = await PaymentIntent.find(
            PaymentIntent.status == PaymentIntentStatus.SUCCEEDED
        ).to_list()
        
        for payment in payments:
            ledger_entries = await FinancialLedgerEntry.find(
                FinancialLedgerEntry.reference_id == payment.id
            ).to_list()
            
            if not ledger_entries:
                discrepancies.append({
                    "type": "missing_ledger",
                    "payment_id": payment.id,
                    "user_id": payment.user_id,
                    "amount": payment.credits_amount
                })
        
        return discrepancies

_reconciliation_service = None

def get_reconciliation_service():
    global _reconciliation_service
    if _reconciliation_service is None:
        _reconciliation_service = ReconciliationService()
    return _reconciliation_service
