import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from backend.models.device_fingerprint import DeviceFingerprint
from backend.models.fraud_alert import FraudAlert
from backend.models.user import User
from backend.services.audit import log_event
from backend.config import settings
from beanie import PydanticObjectId

KNOWN_BAD_IPS = set()


def load_ip_blocklist():
    global KNOWN_BAD_IPS
    blocklist_file = getattr(settings, "FRAUD_BLOCKLIST_FILE", None)
    if blocklist_file and os.path.exists(blocklist_file):
        with open(blocklist_file, "r") as f:
            KNOWN_BAD_IPS = {line.strip() for line in f if line.strip()}


load_ip_blocklist()


async def score_action(
    action_type: str,
    fingerprint: DeviceFingerprint,
    user: Optional[User],
    metadata: dict
) -> dict:
    score = 0
    reasons = []
    
    if fingerprint.ip in KNOWN_BAD_IPS:
        score += 40
        reasons.append("IP in known bad list")
    
    if action_type == "purchase":
        amount_cents = metadata.get("amount_cents", 0)
        high_value_threshold = getattr(settings, "HIGH_VALUE_PURCHASE_CENTS", 50000)
        
        if amount_cents > high_value_threshold and fingerprint.usage_count == 1:
            score += 25
            reasons.append(f"High-value purchase (${amount_cents/100:.2f}) with new device")
    
    velocity_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_same_fp = await DeviceFingerprint.find(
        DeviceFingerprint.fingerprint_hash == fingerprint.fingerprint_hash,
        DeviceFingerprint.last_seen >= velocity_cutoff
    ).to_list()
    
    distinct_ips = len(set(fp.ip for fp in recent_same_fp))
    if distinct_ips > 3:
        score += 30
        reasons.append(f"Fingerprint used from {distinct_ips} IPs in 24h")
    
    action = "allow"
    if score >= 70:
        action = "block"
    elif score >= 40:
        action = "verify"
    
    risk_entry = {
        "score": score,
        "reasons": reasons,
        "action": action,
        "action_type": action_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    fingerprint.risk_history.append(risk_entry)
    await fingerprint.save()
    
    if score >= 70:
        alert = FraudAlert(
            user_id=user.id if user else None,
            session_id=fingerprint.session_id,
            ip=fingerprint.ip,
            fingerprint_hash=fingerprint.fingerprint_hash,
            score=score,
            rule_triggered=", ".join(reasons[:3]),
            metadata={
                **metadata,
                "action_type": action_type,
                "all_reasons": reasons
            },
            created_at=datetime.now(timezone.utc)
        )
        await alert.insert()
        
        await log_event(
            actor_user_id=user.id if user else None,
            actor_ip=fingerprint.ip,
            action="fraud_alert_created",
            details={
                "score": score,
                "reasons": reasons,
                "action_type": action_type,
                "fingerprint_hash": fingerprint.fingerprint_hash,
                "alert_id": str(alert.id)
            },
            severity="error"
        )
    
    return {
        "score": score,
        "reasons": reasons,
        "action": action
    }


async def reload_blocklist():
    load_ip_blocklist()
    return len(KNOWN_BAD_IPS)