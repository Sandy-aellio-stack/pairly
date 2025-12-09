import re
from typing import Any, Dict, List


class LogSanitizer:
    """Sanitize sensitive data from logs"""
    
    SENSITIVE_KEYS = [
        'password', 'secret', 'token', 'authorization', 'api_key',
        'access_key', 'private_key', 'credit_card', 'cvv', 'ssn',
        'auth', 'jwt', 'bearer', 'key', 'pwd'
    ]
    
    # Patterns for sensitive data
    CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if cls._is_sensitive_key(key):
                sanitized[key] = cls._redact_value(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def _is_sensitive_key(cls, key: str) -> bool:
        """Check if key name indicates sensitive data"""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in cls.SENSITIVE_KEYS)
    
    @classmethod
    def _redact_value(cls, value: Any) -> str:
        """Redact sensitive value"""
        if not value:
            return '[REDACTED]'
        
        value_str = str(value)
        if len(value_str) <= 4:
            return '***'
        
        # Show last 4 characters for identification
        return f"***{value_str[-4:]}"
    
    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """Sanitize sensitive patterns in string"""
        # Redact credit card numbers
        text = cls.CARD_PATTERN.sub('****-****-****-****', text)
        return text
