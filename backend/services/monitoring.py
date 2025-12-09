import logging
from datetime import datetime, timezone, timedelta
from backend.models.payment_intent import PaymentIntent, PaymentIntentStatus
from backend.models.webhook_event import WebhookEvent, WebhookEventStatus
from backend.models.financial_ledger import FinancialLedgerEntry
from backend.models.credits_transaction import CreditsTransaction

logger = logging.getLogger('service.monitoring')

class MetricsService:
    async def get_payment_metrics(self):
        payments = await PaymentIntent.find_all().to_list()
        
        return {
            "payments_created_total": len(payments),
            "payments_succeeded": sum(1 for p in payments if p.status == PaymentIntentStatus.SUCCEEDED),
            "payments_failed": sum(1 for p in payments if p.status == PaymentIntentStatus.FAILED),
            "payments_pending": sum(1 for p in payments if p.status == PaymentIntentStatus.PENDING),
            "payments_revenue_total": sum(p.amount_cents for p in payments if p.status == PaymentIntentStatus.SUCCEEDED)
        }
    
    async def get_webhook_metrics(self):
        webhooks = await WebhookEvent.find_all().to_list()
        
        return {
            "webhooks_received_total": len(webhooks),
            "webhooks_processed": sum(1 for w in webhooks if w.status == WebhookEventStatus.PROCESSED),
            "webhooks_failed": sum(1 for w in webhooks if w.status == WebhookEventStatus.FAILED),
            "webhooks_pending": sum(1 for w in webhooks if w.status == WebhookEventStatus.PENDING)
        }
    
    async def get_ledger_metrics(self):
        entries = await FinancialLedgerEntry.find_all().to_list()
        
        return {
            "ledger_entries_total": len(entries),
            "ledger_last_sequence": entries[-1].sequence_number if entries else 0
        }
    
    async def get_fraud_metrics(self):
        payments = await PaymentIntent.find_all().to_list()
        
        return {
            "fraud_flags_total": sum(1 for p in payments if p.fraud_score and p.fraud_score >= 40),
            "fraud_blocks_total": sum(1 for p in payments if p.fraud_score and p.fraud_score >= 70)
        }
    
    async def get_credits_metrics(self):
        transactions = await CreditsTransaction.find_all().to_list()
        
        return {
            "credits_spent_total": sum(abs(t.amount) for t in transactions if t.amount < 0),
            "credits_added_total": sum(t.amount for t in transactions if t.amount > 0)
        }

class AlertService:
    async def check_webhook_failure_rate(self):
        webhooks = await WebhookEvent.find_all().to_list()
        if not webhooks:
            return None
        
        failed = sum(1 for w in webhooks if w.status == WebhookEventStatus.FAILED)
        failure_rate = failed / len(webhooks) * 100
        
        if failure_rate > 20:
            return {
                "alert": "high_webhook_failure",
                "severity": "critical",
                "message": f"Webhook failure rate is {failure_rate:.1f}%",
                "threshold": 20
            }
        return None
    
    async def check_fraud_spike(self):
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_payments = await PaymentIntent.find(
            PaymentIntent.created_at >= one_hour_ago
        ).to_list()
        
        if not recent_payments:
            return None
        
        blocked = sum(1 for p in recent_payments if p.fraud_score and p.fraud_score >= 70)
        block_rate = blocked / len(recent_payments) * 100
        
        if block_rate > 30:
            return {
                "alert": "fraud_spike",
                "severity": "warning",
                "message": f"Fraud block rate is {block_rate:.1f}% in last hour",
                "threshold": 30
            }
        return None
    
    async def get_all_alerts(self):
        alerts = []
        
        webhook_alert = await self.check_webhook_failure_rate()
        if webhook_alert:
            alerts.append(webhook_alert)
        
        fraud_alert = await self.check_fraud_spike()
        if fraud_alert:
            alerts.append(fraud_alert)
        
        return alerts

_metrics_service = None
_alert_service = None

def get_metrics_service():
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service

def get_alert_service():
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
