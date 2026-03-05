from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os
import logging

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore', env_file='.env')
    
    # Database and Secrets
    MONGODB_URI: str = os.getenv("MONGO_URL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    FRAUD_BLOCKLIST_FILE: str = os.getenv("FRAUD_BLOCKLIST_FILE", "")
    HIGH_VALUE_PURCHASE_CENTS: int = int(os.getenv("HIGH_VALUE_PURCHASE_CENTS", "50000"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/var/log/pairly/app.log")
    
    # Security configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BAN_THRESHOLD: int = int(os.getenv("RATE_LIMIT_BAN_THRESHOLD", "150"))
    RATE_LIMIT_BAN_DURATION: int = int(os.getenv("RATE_LIMIT_BAN_DURATION", "3600"))
    
    # Payment system (Stripe + Razorpay)
    PAYMENTS_ENABLED: bool = os.getenv("PAYMENTS_ENABLED", "true").lower() == "true"
    PAYMENTS_MOCK_MODE: bool = os.getenv("PAYMENTS_MOCK_MODE", "true").lower() == "true"

    # Stripe configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Razorpay configuration (India)
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    
    # Firebase configuration
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "")

settings = Settings()

# Validate critical settings
if not settings.JWT_SECRET:
    logging.error("CRITICAL: JWT_SECRET is not set in environment!")
    # In production, we should probably raise an error here
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("JWT_SECRET must be set in production")

if not settings.MONGODB_URI:
    logging.error("CRITICAL: MONGO_URL is not set in environment!")
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("MONGO_URL must be set in production")

if not settings.REDIS_URL:
    logging.warning("REDIS_URL is not set, defaulting to localhost for development")
    settings.REDIS_URL = "redis://localhost:6379"