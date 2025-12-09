from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore', env_file='.env')
    
    MONGODB_URI: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    FRAUD_BLOCKLIST_FILE: str = ""
    HIGH_VALUE_PURCHASE_CENTS: int = 50000
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/var/log/pairly/app.log")
    
    # Security configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    FRONTEND_URL: str = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:3000")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BAN_THRESHOLD: int = int(os.getenv("RATE_LIMIT_BAN_THRESHOLD", "150"))
    RATE_LIMIT_BAN_DURATION: int = int(os.getenv("RATE_LIMIT_BAN_DURATION", "3600"))
    
    # Payment system (Phase 8)
    PAYMENTS_ENABLED: bool = os.getenv("PAYMENTS_ENABLED", "true").lower() == "true"
    PAYMENTS_MOCK_MODE: bool = os.getenv("PAYMENTS_MOCK_MODE", "true").lower() == "true"
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


settings = Settings()