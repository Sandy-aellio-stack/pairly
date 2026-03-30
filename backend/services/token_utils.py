from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError as JoseExpiredSignatureError
import logging
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from uuid import uuid4
from backend.config import settings

logger = logging.getLogger('service.token')

# Load configuration from environment
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ISSUER = "pairly"
AUDIENCE = "pairly-api"

def create_access_token(user_id: str, role: str, rtid: str, minutes: int = 30):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes)
    jti = str(uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "type": "access",
        "iat": now,
        "exp": exp
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(
        "Access token created",
        extra={
            "user_id": str(user_id),
            "jti": jti
        }
    )
    
    return token

def create_refresh_token(user_id: str, role: str, rtid: str, days: int = 7):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=days)
    jti = str(uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "type": "refresh",
        "iat": now,
        "exp": exp
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return token

def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
            audience=AUDIENCE, 
            issuer=ISSUER
        )
        if payload.get("type") != expected_type and payload.get("token_type") != expected_type:
            raise HTTPException(401, "Invalid token type")
        return payload
    except JoseExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except JWTError:
        raise HTTPException(401, "Invalid token")
