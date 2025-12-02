from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

class Settings(BaseSettings):
    model_config = ConfigDict(extra='ignore', env_file='.env')
    
    MONGODB_URI: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-secret-key-in-production")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    FRAUD_BLOCKLIST_FILE: str = ""
    HIGH_VALUE_PURCHASE_CENTS: int = 50000


settings = Settings()