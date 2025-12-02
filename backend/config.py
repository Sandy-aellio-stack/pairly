from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    JWT_SECRET: str
    REDIS_URL: str = "redis://localhost:6379"
    FRAUD_BLOCKLIST_FILE: str = ""
    HIGH_VALUE_PURCHASE_CENTS: int = 50000

    class Config:
        env_file = ".env"


settings = Settings()