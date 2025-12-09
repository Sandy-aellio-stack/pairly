from fastapi import APIRouter, HTTPException, Depends
from backend.models.user import User
from backend.routes.auth import get_current_user
from backend.services.monitoring import get_metrics_service, get_alert_service
import logging

logger = logging.getLogger('routes.admin_monitoring')
router = APIRouter(prefix="/api/admin", tags=["admin-monitoring"])

def check_admin(user: User):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")

@router.get("/metrics")
async def get_metrics(user: User = Depends(get_current_user)):
    check_admin(user)
    
    metrics_service = get_metrics_service()
    
    payment_metrics = await metrics_service.get_payment_metrics()
    webhook_metrics = await metrics_service.get_webhook_metrics()
    ledger_metrics = await metrics_service.get_ledger_metrics()
    fraud_metrics = await metrics_service.get_fraud_metrics()
    credits_metrics = await metrics_service.get_credits_metrics()
    
    return {
        **payment_metrics,
        **webhook_metrics,
        **ledger_metrics,
        **fraud_metrics,
        **credits_metrics
    }

@router.get("/alerts")
async def get_alerts(user: User = Depends(get_current_user)):
    check_admin(user)
    
    alert_service = get_alert_service()
    alerts = await alert_service.get_all_alerts()
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "status": "critical" if any(a.get("severity") == "critical" for a in alerts) else "ok"
    }
