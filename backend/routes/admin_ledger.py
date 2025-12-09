from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime
from backend.models.user import User
from backend.models.financial_ledger import FinancialLedgerEntry, LedgerEntryType
from backend.routes.auth import get_current_user
from backend.services.ledger import get_ledger_service
import logging

logger = logging.getLogger('routes.admin_ledger')
router = APIRouter(prefix="/api/admin/ledger", tags=["admin-ledger"])

def check_admin(user: User):
    if user.role not in ["admin", "finance_admin"]:
        raise HTTPException(403, "Admin access required")

@router.get("/entries")
async def list_ledger_entries(
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    reference_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    check_admin(user)
    
    query_filters = []
    
    if user_id:
        query_filters.append(
            (FinancialLedgerEntry.debit_account.contains(user_id)) |
            (FinancialLedgerEntry.credit_account.contains(user_id))
        )
    
    if reference_id:
        query_filters.append(FinancialLedgerEntry.reference_id == reference_id)
    
    if entry_type:
        query_filters.append(FinancialLedgerEntry.entry_type == LedgerEntryType(entry_type))
    
    if start_date:
        query_filters.append(FinancialLedgerEntry.created_at >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))
    
    if end_date:
        query_filters.append(FinancialLedgerEntry.created_at <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))
    
    skip = (page - 1) * limit
    
    if query_filters:
        from functools import reduce
        import operator
        combined = reduce(operator.and_, query_filters)
        entries = await FinancialLedgerEntry.find(combined).sort("-sequence_number").skip(skip).limit(limit).to_list()
        total = await FinancialLedgerEntry.find(combined).count()
    else:
        entries = await FinancialLedgerEntry.find_all().sort("-sequence_number").skip(skip).limit(limit).to_list()
        total = await FinancialLedgerEntry.find_all().count()
    
    return {
        "entries": [e.to_dict() for e in entries],
        "pagination": {"page": page, "limit": limit, "total": total}
    }

@router.get("/validate-chain")
async def validate_chain(user: User = Depends(get_current_user)):
    check_admin(user)
    ledger_service = get_ledger_service()
    is_valid, error = await ledger_service.verify_chain_integrity()
    
    return {
        "valid": is_valid,
        "error": error,
        "message": "Chain is valid" if is_valid else f"Chain broken: {error}"
    }

@router.get("/user/{user_id}/statement")
async def get_user_statement(
    user_id: str,
    user: User = Depends(get_current_user)
):
    check_admin(user)
    ledger_service = get_ledger_service()
    
    # Get balance
    balance = await ledger_service.get_account_balance(f"user_credits_{user_id}")
    
    # Get all entries for user
    credit_entries = await FinancialLedgerEntry.find(
        FinancialLedgerEntry.credit_account == f"user_credits_{user_id}"
    ).sort("-created_at").to_list()
    
    debit_entries = await FinancialLedgerEntry.find(
        FinancialLedgerEntry.debit_account == f"user_credits_{user_id}"
    ).sort("-created_at").to_list()
    
    total_credits = sum(e.amount for e in credit_entries)
    total_debits = sum(e.amount for e in debit_entries)
    
    return {
        "user_id": user_id,
        "account": f"user_credits_{user_id}",
        "current_balance": balance.balance,
        "total_credits_in": total_credits,
        "total_credits_out": total_debits,
        "net_credits": total_credits - total_debits,
        "entries": [e.to_dict() for e in (credit_entries + debit_entries)]
    }

@router.get("/export")
async def export_ledger(
    user: User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    check_admin(user)
    
    query_filters = []
    if start_date:
        query_filters.append(FinancialLedgerEntry.created_at >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))
    if end_date:
        query_filters.append(FinancialLedgerEntry.created_at <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))
    
    if query_filters:
        from functools import reduce
        import operator
        entries = await FinancialLedgerEntry.find(reduce(operator.and_, query_filters)).sort("sequence_number").to_list()
    else:
        entries = await FinancialLedgerEntry.find_all().sort("sequence_number").to_list()
    
    return {
        "exported_at": datetime.now().isoformat(),
        "count": len(entries),
        "entries": [e.to_dict() for e in entries]
    }
