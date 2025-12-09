from fastapi import APIRouter, HTTPException, Depends
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.services.reconciliation import get_reconciliation_service
import logging

logger = logging.getLogger('routes.admin_reconciliation')
router = APIRouter(prefix="/api/admin/reconciliation", tags=["admin-reconciliation"])

def check_admin(user: User):
    if user.role not in ["admin", "finance_admin"]:
        raise HTTPException(403, "Admin access required")

@router.get("/run")
async def run_reconciliation(user: User = Depends(get_current_user)):
    check_admin(user)
    service = get_reconciliation_service()
    report = await service.reconcile_payments_vs_ledger()
    
    logger.info(f"Reconciliation run by admin {user.id}")
    return report.to_dict()

@router.get("/latest-report")
async def get_latest_report(user: User = Depends(get_current_user)):
    check_admin(user)
    service = get_reconciliation_service()
    report = await service.reconcile_payments_vs_ledger()
    return report.to_dict()

@router.get("/discrepancies")
async def get_discrepancies(user: User = Depends(get_current_user)):
    check_admin(user)
    service = get_reconciliation_service()
    discrepancies = await service.find_discrepancies()
    return {"discrepancies": discrepancies, "count": len(discrepancies)}

@router.get("/user/{user_id}")
async def reconcile_user(
    user_id: str,
    user: User = Depends(get_current_user)
):
    check_admin(user)
    service = get_reconciliation_service()
    result = await service.reconcile_credits_vs_ledger(user_id)
    return result
