from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os
import logging
from dotenv import load_dotenv

# Load environment variables (override=True ensures .env values take priority)
load_dotenv(override=True)

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore')
    
    # Required for production
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database and Secrets
    MONGODB_URI: str = os.getenv("MONGO_URL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    FRAUD_BLOCKLIST_FILE: str = os.getenv("FRAUD_BLOCKLIST_FILE", "")
    HIGH_VALUE_PURCHASE_CENTS: int = int(os.getenv("HIGH_VALUE_PURCHASE_CENTS", "50000"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/var/log/pairly/app.log")
    
    # Security configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    RATE_LIMIT_BAN_THRESHOLD: int = int(os.getenv("RATE_LIMIT_BAN_THRESHOLD", "150"))
    RATE_LIMIT_BAN_DURATION: int = int(os.getenv("RATE_LIMIT_BAN_DURATION", "3600"))
    
    # Payment system
    PAYMENTS_ENABLED: bool = os.getenv("PAYMENTS_ENABLED", "true").lower() == "true"
    PAYMENTS_MOCK_MODE: bool = os.getenv("PAYMENTS_MOCK_MODE", "true").lower() == "true"

    # Firebase configuration
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "")

settings = Settings()

# CRITICAL VALIDATION
if not settings.JWT_SECRET:
    logging.error("CRITICAL: JWT_SECRET is missing!")
    raise RuntimeError("JWT_SECRET must be set in environment")

if not settings.MONGODB_URI:
    logging.error("CRITICAL: MONGO_URL is missing!")
    raise RuntimeError("MONGO_URL must be set in environment")

if not settings.REDIS_URL:
    logging.warning("REDIS_URL is not set, using default")