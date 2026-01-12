"""
Environment Variable Validation
Ensures all required environment variables are set before app starts
"""
import os
import sys
import re
import logging
from typing import List, Tuple

logger = logging.getLogger("env_validator")


class EnvValidationError(Exception):
    """Raised when required environment variables are missing"""
    pass


# Known weak JWT secrets to reject
WEAK_JWT_PATTERNS = [
    r"change[-_]?(this|me|in[-_]?production)",
    r"^(password|secret|key|token)$",
    r"^your[-_]?secret",
    r"^my[-_]?secret",
    r"^test[-_]?secret",
    r"^dev[-_]?secret",
    r"example|sample|placeholder",
]


def validate_jwt_secret(secret: str, is_production: bool) -> Tuple[bool, List[str]]:
    """
    Validate JWT secret strength.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    if not secret:
        errors.append("JWT_SECRET is required")
        return False, errors
    
    # Minimum length check
    min_length = 64 if is_production else 32
    if len(secret) < min_length:
        errors.append(f"JWT_SECRET must be at least {min_length} characters (currently {len(secret)})")
    
    # Check for weak patterns
    for pattern in WEAK_JWT_PATTERNS:
        if re.search(pattern, secret, re.IGNORECASE):
            errors.append(f"JWT_SECRET contains weak pattern - not suitable for production")
            break
    
    # Production-specific: require character diversity
    if is_production:
        has_upper = bool(re.search(r"[A-Z]", secret))
        has_lower = bool(re.search(r"[a-z]", secret))
        has_digit = bool(re.search(r"[0-9]", secret))
        has_special = bool(re.search(r"[^A-Za-z0-9]", secret))
        
        char_classes = sum([has_upper, has_lower, has_digit, has_special])
        if char_classes < 3:
            errors.append(f"JWT_SECRET needs more character diversity (has {char_classes}/4 types, need 3+)")
    
    return len(errors) == 0, errors


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

    # Special validation for JWT_SECRET
    jwt_secret = os.getenv("JWT_SECRET", "")
    jwt_valid, jwt_errors = validate_jwt_secret(jwt_secret, is_production)
    if not jwt_valid:
        if is_production:
            errors.extend(jwt_errors)
        else:
            for err in jwt_errors:
                warnings.append(f"JWT_SECRET: {err}")

    # Check production-specific vars
    if is_production:
        for var_name, description in production_required_vars:
            value = os.getenv(var_name)
            if not value or value.strip() == "":
                errors.append(f"{var_name} is required in production ({description})")
        
        # Validate CORS is not wildcard in production
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if cors_origins == "*":
            errors.append("CORS_ORIGINS cannot be '*' in production - set specific origins")

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
