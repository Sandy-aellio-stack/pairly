import os
import base64
import hashlib
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if os.getenv("ENVIRONMENT") == "production" and not ENCRYPTION_KEY:
    # Fail fast in production
    raise RuntimeError("ENCRYPTION_KEY must be set in production environment")

if not ENCRYPTION_KEY:
    # Development fallback (explicit)
    print("⚠️  WARNING: Using auto-generated encryption key for development only.")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

# Ensure bytes and valid Fernet key
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

try:
    cipher = Fernet(ENCRYPTION_KEY)
except Exception:
    key_hash = hashlib.sha256(ENCRYPTION_KEY).digest()
    cipher = Fernet(base64.urlsafe_b64encode(key_hash))


def encrypt(data: str) -> str:
    """Encrypt a string and return base64 encoded result."""
    return cipher.encrypt(data.encode()).decode()


def decrypt(encrypted_data: str) -> str:
    """Decrypt a base64 encoded encrypted string."""
    return cipher.decrypt(encrypted_data.encode()).decode()
