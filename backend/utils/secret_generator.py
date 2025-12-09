import secrets
import string
import hashlib
from typing import Tuple


class SecretGenerator:
    """Generate cryptographically secure secrets"""
    
    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate a secure API key"""
        return secrets.token_hex(length)
    
    @staticmethod
    def validate_secret_strength(secret: str) -> Tuple[bool, str, int]:
        """Validate secret strength. Returns (is_valid, reason, score)"""
        if len(secret) < 32:
            return False, "Secret too short (minimum 32 characters)", 0
        
        if len(secret) < 64:
            score = 1  # Weak
            reason = "Secret length acceptable but not recommended"
        else:
            score = 2  # Medium
            reason = "Secret length good"
        
        # Check character diversity
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(c in string.punctuation for c in secret)
        
        diversity = sum([has_upper, has_lower, has_digit, has_special])
        
        if diversity >= 3:
            score = 3  # Strong
            reason = "Secret has good character diversity"
        
        return True, reason, score
    
    @staticmethod
    def hash_secret(secret: str) -> str:
        """Hash secret for tracking (not for security)"""
        return hashlib.sha256(secret.encode()).hexdigest()
