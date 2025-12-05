import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from backend.config import settings
from uuid import uuid4

SECRET = settings.JWT_SECRET
ALG = "HS256"


def create_access_token(user_id: str, role: str, rtid: str, minutes: int = 30):
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": "pairly",
        "aud": "pairly-api",
        "token_type": "access",
        "exp": exp
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)


def create_refresh_token(user_id: str, role: str, rtid: str, days: int = 7):
    exp = datetime.utcnow() + timedelta(days=days)
    jti = str(uuid4())
    payload = {
        "sub": user_id,
        "role": role,
        "rtid": rtid,
        "jti": jti,
        "iss": "pairly",
        "aud": "pairly-api",
        "token_type": "refresh",
        "exp": exp
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)


def verify_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALG], audience="pairly-api", issuer="pairly")
        if payload.get("token_type") != expected_type:
            raise HTTPException(401, "Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")