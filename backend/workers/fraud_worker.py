import asyncio
from datetime import datetime, timedelta
from backend.database import init_db
from backend.models.fraud_alert import FraudAlert
from backend.models.device_fingerprint import DeviceFingerprint
from backend.services.audit import log_event


async def scan_suspicious_patterns():
    print(f"[{datetime.utcnow().isoformat()}] Running fraud pattern scan...")
    
    await init_db()
    
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    try:
        high_velocity_fps = await DeviceFingerprint.aggregate([
            {"$match": {"last_seen": {"$gte": one_hour_ago}}},
            {"$group": {
                "_id": "$fingerprint_hash",
                "ips": {"$addToSet": "$ip"},
                "usage": {"$sum": 1}
            }},
            {"$match": {"$expr": {"$gte": [{"$size": "$ips"}, 5]}}}
        ]).to_list()
        
        for item in high_velocity_fps:
            fp_hash = item["_id"]
            fingerprint = await DeviceFingerprint.find_one(
                DeviceFingerprint.fingerprint_hash == fp_hash
            )
            
            if fingerprint:
                existing_alert = await FraudAlert.find_one(
                    FraudAlert.fingerprint_hash == fp_hash,
                    FraudAlert.created_at >= one_hour_ago
                )
                
                if not existing_alert:
                    alert = FraudAlert(
                        user_id=fingerprint.user_id,
                        session_id=fingerprint.session_id,
                        ip=fingerprint.ip,
                        fingerprint_hash=fp_hash,
                        score=80,
                        rule_triggered="High velocity IP changes",
                        metadata={
                            "ip_count": len(item["ips"]),
                            "usage": item["usage"],
                            "ips": item["ips"]
                        },
                        created_at=now
                    )
                    await alert.insert()
                    
                    print(f"  → Created alert for fingerprint {fp_hash[:8]}... (score: 80)")
                    
                    await log_event(
                        actor_user_id=fingerprint.user_id,
                        actor_ip=fingerprint.ip,
                        action="fraud_pattern_detected",
                        details={
                            "pattern": "high_velocity",
                            "fingerprint_hash": fp_hash,
                            "ip_count": len(item["ips"])
                        },
                        severity="warning"
                    )
    except Exception as e:
        print(f"  ✗ Error in high-velocity scan: {e}")
    
    print(f"[{datetime.utcnow().isoformat()}] Fraud scan complete")


async def main():
    print("=" * 60)
    print("Fraud Detection Worker Started")
    print("=" * 60)
    
    while True:
        try:
            await scan_suspicious_patterns()
        except Exception as e:
            print(f"✗ Worker error: {e}")
        
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())