"""
Environment Variable Validation
Ensures all required environment variables are set before app starts
"""
import os
import sys
import logging
from typing import List, Tuple

logger = logging.getLogger("env_validator")


class EnvValidationError(Exception):
    """Raised when required environment variables are missing"""
    pass


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate required environment variables.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    warnings = []

    environment = os.getenv("ENVIRONMENT", "development")
    is_production = environment == "production"

    # Required for ALL environments
    required_vars = [
        ("MONGO_URL", "MongoDB connection string"),
        ("JWT_SECRET", "JWT signing secret (must be strong)"),
        ("REDIS_URL", "Redis connection URL"),
    ]

    # Required for PRODUCTION only
    production_required_vars = [
        ("FRONTEND_URL", "Frontend URL for CORS"),
        ("ADMIN_EMAIL", "Admin panel login email"),
        ("ADMIN_PASSWORD", "Admin panel login password"),
    ]

    # Check required vars
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if not value or value.strip() == "":
            errors.append(f"{var_name} is required ({description})")
        elif var_name == "JWT_SECRET" and len(value) < 32:
            errors.append(f"{var_name} must be at least 32 characters long (currently {len(value)})")

    # Check production-specific vars
    if is_production:
        for var_name, description in production_required_vars:
            value = os.getenv(var_name)
            if not value or value.strip() == "":
                errors.append(f"{var_name} is required in production ({description})")

    # Optional but recommended
    recommended_vars = [
        ("STRIPE_SECRET_KEY", "Stripe payment integration"),
        ("STRIPE_WEBHOOK_SECRET", "Stripe webhook verification"),
        ("RAZORPAY_KEY_ID", "Razorpay payment integration (India)"),
        ("RAZORPAY_KEY_SECRET", "Razorpay secret key"),
    ]

    for var_name, description in recommended_vars:
        value = os.getenv(var_name)
        if not value and is_production:
            warnings.append(f"{var_name} not set - {description} will not work")

    # Validate MongoDB URL format
    mongo_url = os.getenv("MONGO_URL", "")
    if mongo_url and not mongo_url.startswith(("mongodb://", "mongodb+srv://")):
        errors.append("MONGO_URL must start with 'mongodb://' or 'mongodb+srv://'")

    # Validate Redis URL format
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url and not redis_url.startswith(("redis://", "rediss://")):
        errors.append("REDIS_URL must start with 'redis://' or 'rediss://'")

    # Log results
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")

    if warnings:
        logger.warning("Environment validation warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    if not errors and not warnings:
        logger.info("Environment validation passed - all required variables set")
    elif not errors:
        logger.info("Environment validation passed with warnings")

    return len(errors) == 0, errors


def validate_or_exit():
    """
    Validate environment and exit if validation fails.
    Should be called at application startup.
    """
    is_valid, errors = validate_environment()

    if not is_valid:
        logger.critical("=" * 80)
        logger.critical("ENVIRONMENT VALIDATION FAILED")
        logger.critical("=" * 80)
        logger.critical("The following required environment variables are missing or invalid:")
        for error in errors:
            logger.critical(f"  ❌ {error}")
        logger.critical("")
        logger.critical("Please set these variables in your .env file or environment")
        logger.critical("=" * 80)
        sys.exit(1)

    return True


def get_validation_report() -> dict:
    """Get environment validation report as dict"""
    is_valid, errors = validate_environment()

    return {
        "valid": is_valid,
        "errors": errors,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "mongo_url": bool(os.getenv("MONGO_URL")),
            "jwt_secret": bool(os.getenv("JWT_SECRET")),
            "redis_url": bool(os.getenv("REDIS_URL")),
            "admin_configured": bool(os.getenv("ADMIN_EMAIL") and os.getenv("ADMIN_PASSWORD")),
            "payments_configured": bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("RAZORPAY_KEY_ID")),
        }
    }
