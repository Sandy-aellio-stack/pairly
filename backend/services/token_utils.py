import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from backend.core.secrets_manager import secrets_manager
from uuid import uuid4

logger = logging.getLogger('service.token')

ALG = "HS256"


def _get_secret() -> str:
    """Get JWT secret from secrets manager"""
    secret = secrets_manager.get_secret('JWT_SECRET')
    if not secret:
        raise ValueError("JWT_SECRET not configured")
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
    
    logger.info(
        "Access token created",
        extra={
            "event": "token_created",
            "user_id": user_id,
            "token_type": "access",
            "jti": jti,
            "expires_at": exp.isoformat()
        }
    )
    
    return token


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
    
    logger.info(
        "Refresh token created",
        extra={
            "event": "token_created",
            "user_id": user_id,
            "token_type": "refresh",
            "jti": jti
        }
    )
    
    return token


def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[ALG], audience="pairly-api", issuer="pairly")
        if payload.get("token_type") != expected_type:
            logger.warning(
                "Token type mismatch",
                extra={"expected": expected_type, "actual": payload.get("token_type")}
            )
            raise HTTPException(401, "Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired", extra={"event": "token_expired"})
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}", extra={"event": "token_invalid"})
        raise HTTPException(401, "Invalid token")
