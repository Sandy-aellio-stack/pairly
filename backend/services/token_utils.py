import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from backend.core.secrets_manager import secrets_manager
from uuid import uuid4

logger = logging.getLogger('service.token')

ALG = "HS256"


def _get_secret() -> str:
    \"\"\"Get JWT secret from secrets manager\"\"\"
    secret = secrets_manager.get_secret('JWT_SECRET')
    if not secret:
        raise ValueError(\"JWT_SECRET not configured\")
    return secret


def create_access_token(user_id: str, role: str, rtid: str, minutes: int = 30):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes)
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": "pairly",
        "aud": "pairly-api",
        "token_type": "access",
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }
    
    token = jwt.encode(payload, _get_secret(), algorithm=ALG)
    
    logger.info(\n        \"Access token created\",\n        extra={\n            \"event\": \"token_created\",\n            \"user_id\": user_id,\n            \"token_type\": \"access\",\n            \"jti\": jti,\n            \"expires_at\": exp.isoformat()\n        }\n    )\n    \n    return token


def create_refresh_token(user_id: str, role: str, rtid: str, days: int = 7):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=days)
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": "pairly",
        "aud": "pairly-api",
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }
    
    token = jwt.encode(payload, _get_secret(), algorithm=ALG)
    
    logger.info(\n        \"Refresh token created\",\n        extra={\n            \"event\": \"token_created\",\n            \"user_id\": user_id,\n            \"token_type\": \"refresh\",\n            \"jti\": jti\n        }\n    )\n    \n    return token


def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[ALG], audience="pairly-api", issuer="pairly")
        if payload.get("token_type") != expected_type:
            logger.warning(\n                \"Token type mismatch\",\n                extra={\"expected\": expected_type, \"actual\": payload.get(\"token_type\")}\n            )\n            raise HTTPException(401, "Invalid token type")\n        return payload\n    except jwt.ExpiredSignatureError:
        logger.warning(\"Token expired\", extra={\"event\": \"token_expired\"})\n        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:\n        logger.warning(f\"Invalid token: {str(e)}\", extra={\"event\": \"token_invalid\"})\n        raise HTTPException(401, "Invalid token")