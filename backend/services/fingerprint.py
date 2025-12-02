import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request
from backend.models.device_fingerprint import DeviceFingerprint
from backend.config import settings
from beanie import PydanticObjectId


def parse_user_agent(user_agent: str) -> dict:
    ua_lower = user_agent.lower()
    
    browser = "unknown"
    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "chrome"
    elif "firefox" in ua_lower:
        browser = "firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "safari"
    elif "edg" in ua_lower:
        browser = "edge"
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser = "opera"
    
    os = "unknown"
    if "windows" in ua_lower:
        os = "windows"
    elif "mac" in ua_lower or "darwin" in ua_lower:
        os = "macos"
    elif "linux" in ua_lower:
        os = "linux"
    elif "android" in ua_lower:
        os = "android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os = "ios"
    
    device_type = "desktop"
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"
    
    return {
        "browser": browser,
        "os": os,
        "device_type": device_type
    }


def normalize_fingerprint_data(ip: str, user_agent: str, accept_lang: Optional[str], device_info: dict) -> str:
    normalized = {
        "ip": ip.strip().lower(),
        "user_agent": user_agent.strip()[:500],
        "accept_lang": (accept_lang or "").strip().lower()[:50],
        "browser": device_info.get("browser", "unknown"),
        "os": device_info.get("os", "unknown"),
        "device_type": device_info.get("device_type", "unknown")
    }
    
    canonical = json.dumps(normalized, sort_keys=True)
    
    fingerprint_hash = hmac.new(
        settings.JWT_SECRET.encode(),
        canonical.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return fingerprint_hash


async def register_fingerprint(
    request: Optional[Request] = None,
    user_id: Optional[PydanticObjectId] = None,
    session_id: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    accept_lang: Optional[str] = None,
    device_info: Optional[dict] = None
) -> DeviceFingerprint:
    
    if request:
        ip = ip or (request.client.host if request.client else "unknown")
        user_agent = user_agent or request.headers.get("user-agent", "unknown")
        accept_lang = accept_lang or request.headers.get("accept-language")
    
    ip = ip or "unknown"
    user_agent = user_agent or "unknown"
    
    parsed_device = parse_user_agent(user_agent)
    device_info = device_info or parsed_device
    
    fingerprint_hash = normalize_fingerprint_data(ip, user_agent, accept_lang, device_info)
    
    existing = await DeviceFingerprint.find_one(
        DeviceFingerprint.fingerprint_hash == fingerprint_hash
    )
    
    if existing:
        existing.last_seen = datetime.utcnow()
        existing.usage_count += 1
        if user_id and not existing.user_id:
            existing.user_id = user_id
        if session_id:
            existing.session_id = session_id
        await existing.save()
        return existing
    
    fingerprint = DeviceFingerprint(
        user_id=user_id,
        session_id=session_id,
        ip=ip,
        user_agent=user_agent,
        accept_lang=accept_lang,
        device_info=device_info,
        fingerprint_hash=fingerprint_hash,
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    
    await fingerprint.insert()
    return fingerprint


async def get_fingerprint_history(fingerprint_hash: str) -> Optional[DeviceFingerprint]:
    return await DeviceFingerprint.find_one(
        DeviceFingerprint.fingerprint_hash == fingerprint_hash
    )


async def get_user_fingerprints(user_id: PydanticObjectId, days: int = 7) -> list:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return await DeviceFingerprint.find(
        DeviceFingerprint.user_id == user_id,
        DeviceFingerprint.last_seen >= cutoff
    ).to_list()