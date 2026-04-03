import os
import json
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger("firebase_auth")


def _init_firebase_app():
    # Initialize firebase app once. Supports either file path or JSON string in env.
    if firebase_admin._apps:
        return firebase_admin._apps[list(firebase_admin._apps.keys())[0]]

    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if sa_path and os.path.exists(sa_path):
        cred = credentials.Certificate(sa_path)
    elif sa_json:
        try:
            sa_obj = json.loads(sa_json)
            cred = credentials.Certificate(sa_obj)
        except Exception as e:
            logger.error(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            raise
    else:
        # Use application default credentials if provided in environment
        cred = credentials.ApplicationDefault()

    app = firebase_admin.initialize_app(cred)
    logger.info("Firebase app initialized for admin auth")
    return app


def verify_firebase_token(token: str) -> Optional[dict]:
    """Verify an Firebase ID token and return the decoded token dict.

    Raises an exception on failure.
    """
    if not firebase_admin._apps:
        _init_firebase_app()

    # firebase-admin expects a plain ID token (not 'Bearer ...')
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    decoded = auth.verify_id_token(token)
    return decoded
