import os
import logging
from typing import Optional, Dict, Any
from backend.utils.secret_generator import SecretGenerator

logger = logging.getLogger('core.secrets')


class SecretsManager:
    """Centralized secrets management with validation"""
    
    REQUIRED_SECRETS = ['JWT_SECRET', 'MONGODB_URI']
    
    WEAK_DEFAULTS = [
        'change-this-secret-key-in-production',
        'your-secret-key',
        'secret',
        'password',
        '12345',
    ]
    
    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from environment"""
        for key in self.REQUIRED_SECRETS:
            value = os.getenv(key)
            if not value:
                if key == 'JWT_SECRET':
                    # Generate secure secret if not provided in development
                    env = os.getenv('ENVIRONMENT', 'development')
                    if env == 'development':
                        value = SecretGenerator.generate_jwt_secret()
                        logger.warning(f"Generated temporary JWT_SECRET for development")
                    else:
                        raise ValueError(f"Required secret {key} not found in environment")
            self._secrets[key] = value
        
        # Validate secrets in production
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production':
            self._validate_production_secrets()
    
    def _validate_production_secrets(self):
        """Validate secrets are production-ready"""
        jwt_secret = self._secrets.get('JWT_SECRET', '')
        
        # Check for weak defaults
        if any(weak in jwt_secret.lower() for weak in self.WEAK_DEFAULTS):
            raise ValueError("Weak JWT_SECRET detected in production")
        
        # Check strength
        is_valid, reason, score = SecretGenerator.validate_secret_strength(jwt_secret)
        if not is_valid or score < 2:
            raise ValueError(f"JWT_SECRET not strong enough for production: {reason}")
        
        logger.info("All secrets validated for production")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value"""
        return self._secrets.get(key) or os.getenv(key, default)
    
    def is_production_ready(self) -> bool:
        """Check if all required secrets are configured"""
        try:
            for key in self.REQUIRED_SECRETS:
                if not self._secrets.get(key):
                    return False
            return True
        except:
            return False


# Global instance
secrets_manager = SecretsManager()
