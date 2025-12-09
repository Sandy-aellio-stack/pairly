import logging
import os
from backend.core.secrets_manager import secrets_manager

logger = logging.getLogger('core.security')


class SecurityValidator:
    """Validate security configuration on startup"""
    
    @staticmethod
    def validate_all():
        """Run all security validations"""
        logger.info("Running security validation checks")
        
        SecurityValidator.validate_jwt_secret()
        SecurityValidator.validate_environment()
        SecurityValidator.validate_cors_config()
        
        logger.info("Security validation completed successfully")
    
    @staticmethod
    def validate_jwt_secret():
        """Validate JWT secret configuration"""
        jwt_secret = secrets_manager.get_secret('JWT_SECRET')
        
        if not jwt_secret:
            raise ValueError("JWT_SECRET is not configured")
        
        if len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET is too short (minimum 32 characters)")
        
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production' and len(jwt_secret) < 64:
            logger.warning("JWT_SECRET length < 64 chars in production (recommended: 64+)")
        
        logger.info("JWT secret validation passed")
    
    @staticmethod
    def validate_environment():
        """Validate environment configuration"""
        env = os.getenv('ENVIRONMENT', 'development')
        valid_envs = ['development', 'staging', 'production']
        
        if env not in valid_envs:
            logger.warning(f"Unknown ENVIRONMENT: {env}. Valid options: {valid_envs}")
        
        logger.info(f"Environment: {env}")
    
    @staticmethod
    def validate_cors_config():
        """Validate CORS configuration"""
        cors_origins = os.getenv('CORS_ORIGINS', '')
        env = os.getenv('ENVIRONMENT', 'development')
        
        if env == 'production' and not cors_origins:
            logger.warning("CORS_ORIGINS not configured in production - using defaults")
        
        if env == 'production' and '*' in cors_origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' in production")
        
        logger.info("CORS configuration validated")
