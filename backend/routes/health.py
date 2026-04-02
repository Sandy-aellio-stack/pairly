from fastapi import APIRouter
from datetime import datetime, timezone
import os

router = APIRouter(prefix="/health", tags=["System"])

@router.get("")
async def health_check():
    """
    Standard health check endpoint for production monitoring.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }
