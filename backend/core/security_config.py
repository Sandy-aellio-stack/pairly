"""
Security Configuration Module
Centralized security settings with environment-based configuration
"""
import os
import re
import secrets
import hashlib
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("security.config")


@dataclass
class SecurityConfig:
    """Centralized security configuration"""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    # CORS Configuration
    cors_origins: List[str] = field(default_factory=list)
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["Authorization", "Content-Type", "X-Request-ID"])
    cors_max_age: int = 600  # 10 minutes
    
    # Security Headers
    enable_hsts: bool = False
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    
    content_security_policy: str = ""
    permissions_policy: str = ""
    
    # JWT Configuration
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_issuer: str = "truebond"
    jwt_audience: str = "truebond-api"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    
    def __post_init__(self):
        """Initialize configuration based on environment"""
        self._configure_for_environment()
    
    def _configure_for_environment(self):
        """Set configuration based on environment"""
        if self.environment == "production":
            self._configure_production()
        elif self.environment == "staging":
            self._configure_staging()
        else:
            self._configure_development()
    
    def _configure_production(self):
        """Production security configuration - strictest settings"""
        # CORS - Only allow configured frontend URL
        frontend_url = os.getenv("FRONTEND_URL", "").strip()
        allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
        
        self.cors_origins = []
        
        if frontend_url:
            self.cors_origins.append(frontend_url)
        
        if allowed_origins_env:
            additional = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
            self.cors_origins.extend(additional)
        
        if not self.cors_origins:
            logger.critical("PRODUCTION: No CORS origins configured! Set FRONTEND_URL or CORS_ALLOWED_ORIGINS")
            # Fail closed - no CORS in production without explicit config
            self.cors_origins = []
        
        # Remove wildcards in production
        self.cors_origins = [o for o in self.cors_origins if o != "*"]
        
        # Strict headers only
        self.cors_allow_headers = [
            "Authorization",
            "Content-Type", 
            "X-Request-ID",
            "X-CSRF-Token",
        ]
        
        # HSTS enabled
        self.enable_hsts = True
        self.hsts_preload = True
        
        # Content Security Policy
        self.content_security_policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Permissions Policy
        self.permissions_policy = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(self), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        logger.info(f"PRODUCTION security config: CORS origins = {self.cors_origins}")
    
    def _configure_staging(self):
        """Staging security configuration - production-like but with some flexibility"""
        frontend_url = os.getenv("FRONTEND_URL", "").strip()
        allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
        
        self.cors_origins = []
        
        if frontend_url:
            self.cors_origins.append(frontend_url)
        
        if allowed_origins_env:
            additional = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
            self.cors_origins.extend(additional)
        
        # Allow localhost for staging testing
        self.cors_origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ])
        
        # Remove duplicates
        self.cors_origins = list(set(self.cors_origins))
        
        # HSTS enabled but no preload
        self.enable_hsts = True
        self.hsts_preload = False
        
        # Relaxed CSP for staging
        self.content_security_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'self'"
        )
        
        logger.info(f"STAGING security config: CORS origins = {self.cors_origins}")
    
    def _configure_development(self):
        """Development security configuration - permissive for local development"""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        self.cors_origins = [
            frontend_url,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
        ]
        
        # Also check CORS_ORIGINS env var for development
        cors_env = os.getenv("CORS_ORIGINS", "").strip()
        if cors_env == "*":
            # Allow wildcard in development only
            self.cors_origins = ["*"]
        elif cors_env:
            additional = [o.strip() for o in cors_env.split(",") if o.strip()]
            self.cors_origins.extend(additional)
        
        # Remove duplicates (unless wildcard)
        if "*" not in self.cors_origins:
            self.cors_origins = list(set(self.cors_origins))
        
        # More permissive headers for development
        self.cors_allow_headers = ["*"]
        
        # No HSTS in development
        self.enable_hsts = False
        
        # Very permissive CSP for development
        self.content_security_policy = ""
        
        logger.info(f"DEVELOPMENT security config: CORS origins = {self.cors_origins}")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"


class JWTSecretValidator:
    """Validate JWT secret strength and rotation readiness"""
    
    # Minimum requirements
    MIN_LENGTH = 32
    MIN_ENTROPY_BITS = 128
    
    # Weak patterns to reject
    WEAK_PATTERNS = [
        r"^(password|secret|key|token|jwt)[-_]?",
        r"change[-_]?(this|me|in[-_]?production)",
        r"^[a-z]+$",  # All lowercase letters
        r"^[A-Z]+$",  # All uppercase letters
        r"^[0-9]+$",  # All numbers
        r"(.)\1{3,}",  # Same character repeated 4+ times
        r"^(test|dev|staging|prod)[-_]?",
        r"default|example|sample",
    ]
    
    # Common weak secrets
    KNOWN_WEAK_SECRETS = {
        "secret",
        "password",
        "123456",
        "jwt-secret",
        "my-secret-key",
        "change-this",
        "your-secret-here",
        "supersecret",
    }
    
    @classmethod
    def validate(cls, secret: str, environment: str = "development") -> Tuple[bool, List[str], dict]:
        """
        Validate JWT secret strength.
        
        Returns:
            Tuple of (is_valid, errors, metrics)
        """
        errors = []
        warnings = []
        
        # Calculate metrics
        length = len(secret)
        entropy = cls._calculate_entropy(secret)
        has_upper = bool(re.search(r"[A-Z]", secret))
        has_lower = bool(re.search(r"[a-z]", secret))
        has_digit = bool(re.search(r"[0-9]", secret))
        has_special = bool(re.search(r"[^A-Za-z0-9]", secret))
        char_classes = sum([has_upper, has_lower, has_digit, has_special])
        
        metrics = {
            "length": length,
            "entropy_bits": entropy,
            "character_classes": char_classes,
            "has_uppercase": has_upper,
            "has_lowercase": has_lower,
            "has_digits": has_digit,
            "has_special": has_special,
        }
        
        # Length check
        if length < cls.MIN_LENGTH:
            errors.append(f"Secret too short: {length} chars (minimum: {cls.MIN_LENGTH})")
        
        # Entropy check
        if entropy < cls.MIN_ENTROPY_BITS:
            errors.append(f"Secret entropy too low: {entropy:.0f} bits (minimum: {cls.MIN_ENTROPY_BITS})")
        
        # Check for known weak secrets
        if secret.lower() in cls.KNOWN_WEAK_SECRETS:
            errors.append("Secret matches a known weak/common secret")
        
        # Check for weak patterns
        for pattern in cls.WEAK_PATTERNS:
            if re.search(pattern, secret, re.IGNORECASE):
                errors.append(f"Secret contains weak pattern: {pattern}")
                break
        
        # Character class diversity (production requirement)
        if environment == "production" and char_classes < 3:
            errors.append(f"Secret needs more character diversity: {char_classes}/4 classes (need 3+)")
        
        # Production-specific: stricter requirements
        if environment == "production":
            if length < 64:
                warnings.append(f"Production: recommend 64+ chars (current: {length})")
            if entropy < 256:
                warnings.append(f"Production: recommend 256+ entropy bits (current: {entropy:.0f})")
        
        is_valid = len(errors) == 0
        
        if warnings:
            for w in warnings:
                logger.warning(f"JWT Secret: {w}")
        
        return is_valid, errors, metrics
    
    @classmethod
    def _calculate_entropy(cls, secret: str) -> float:
        """Calculate Shannon entropy in bits"""
        if not secret:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in secret:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        length = len(secret)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            if p > 0:
                entropy -= p * (p.bit_length() - 1 + (1 - 1/p if p < 1 else 0))
        
        # Approximate entropy based on character set size
        char_set_size = len(set(secret))
        import math
        bits_per_char = math.log2(max(char_set_size, 1))
        
        return bits_per_char * length
    
    @classmethod
    def generate_secure_secret(cls, length: int = 64) -> str:
        """Generate a cryptographically secure secret"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def get_rotation_info(cls, secret: str) -> dict:
        """Get information about secret rotation readiness"""
        # Hash the secret for safe logging/comparison
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()[:16]
        
        return {
            "secret_identifier": f"sha256:{secret_hash}...",
            "supports_rotation": True,
            "rotation_steps": [
                "1. Generate new secret with generate_secure_secret()",
                "2. Set JWT_SECRET_NEW environment variable with new secret",
                "3. Deploy - app will accept both old and new secrets",
                "4. Wait for all old tokens to expire (7 days for refresh tokens)",
                "5. Set JWT_SECRET to new value, remove JWT_SECRET_NEW",
                "6. Deploy final configuration",
            ],
            "recommended_rotation_interval_days": 90,
        }


# Global security configuration instance
security_config = SecurityConfig()

# Validation function for startup
def validate_security_config() -> Tuple[bool, List[str]]:
    """
    Validate security configuration at startup.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Validate JWT secret
    jwt_secret = os.getenv("JWT_SECRET", "")
    if jwt_secret:
        is_valid, jwt_errors, metrics = JWTSecretValidator.validate(jwt_secret, environment)
        if not is_valid and environment == "production":
            errors.extend([f"JWT: {e}" for e in jwt_errors])
        elif not is_valid:
            for e in jwt_errors:
                logger.warning(f"JWT Secret (non-blocking): {e}")
    else:
        if environment == "production":
            errors.append("JWT_SECRET is required in production")
    
    # Validate CORS in production
    if environment == "production":
        cors_origins = os.getenv("CORS_ORIGINS", "")
        frontend_url = os.getenv("FRONTEND_URL", "")
        allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        
        if cors_origins == "*":
            errors.append("CORS wildcard (*) not allowed in production")
        
        if not frontend_url and not allowed_origins:
            errors.append("FRONTEND_URL or CORS_ALLOWED_ORIGINS required in production")
    
    return len(errors) == 0, errors
