import logging
import hmac
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger('webhook.signature')


class WebhookSignatureVerifier:
    """
    Webhook signature verification service.
    
    Mock Mode: Simulates HMAC-SHA256 signature verification
    Production Mode: Uses real provider SDKs
    """
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        
        if mock_mode:
            logger.info("WebhookSignatureVerifier running in MOCK MODE")
    
    def verify_stripe_signature(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
        tolerance: int = 300  # 5 minutes
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify Stripe webhook signature.
        
        Stripe signature format: t=timestamp,v1=signature
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: Stripe-Signature header value
            webhook_secret: Webhook signing secret
            tolerance: Timestamp tolerance in seconds
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.mock_mode:
            return self._verify_stripe_mock(signature_header, tolerance)
        
        try:
            # Parse signature header
            parts = {}
            for part in signature_header.split(','):
                key, value = part.split('=', 1)
                parts[key.strip()] = value.strip()
            
            timestamp = int(parts.get('t', 0))
            signature = parts.get('v1', '')
            
            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance:
                return False, f"Timestamp outside tolerance window ({tolerance}s)"
            
            # Compute expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Signature mismatch"
            
            logger.info("Stripe signature verified successfully")
            return True, None
        
        except Exception as e:
            logger.error(f"Stripe signature verification error: {e}")
            return False, f"Verification error: {str(e)}"
    
    def _verify_stripe_mock(
        self,
        signature_header: str,
        tolerance: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Mock Stripe signature verification.
        
        Accepts signatures that:
        - Have the correct format (t=timestamp,v1=signature)
        - Have a signature that's not empty
        - Have a timestamp within tolerance
        """
        try:
            # Check header format
            if not signature_header or 't=' not in signature_header or 'v1=' not in signature_header:
                return False, "Invalid signature format"
            
            # Parse timestamp
            parts = {}
            for part in signature_header.split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    parts[key.strip()] = value.strip()
            
            timestamp = int(parts.get('t', 0))
            signature = parts.get('v1', '')
            
            # Check signature not empty
            if not signature or len(signature) < 10:
                return False, "Empty or invalid signature"
            
            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance:
                return False, f"Timestamp outside tolerance ({tolerance}s)"
            
            logger.info("MOCK: Stripe signature verified")
            return True, None
        
        except Exception as e:
            return False, f"Mock verification error: {str(e)}"
    
    def verify_razorpay_signature(
        self,
        payload: bytes,
        signature_header: str,
        webhook_secret: str,
        tolerance: int = 300  # 5 minutes
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify Razorpay webhook signature.
        
        Razorpay uses HMAC-SHA256 on the raw payload.
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: X-Razorpay-Signature header value
            webhook_secret: Webhook signing secret
            tolerance: Timestamp tolerance (for mock mode)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.mock_mode:
            return self._verify_razorpay_mock(signature_header)
        
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if not hmac.compare_digest(signature_header, expected_signature):
                return False, "Signature mismatch"
            
            logger.info("Razorpay signature verified successfully")
            return True, None
        
        except Exception as e:
            logger.error(f"Razorpay signature verification error: {e}")
            return False, f"Verification error: {str(e)}"
    
    def _verify_razorpay_mock(
        self,
        signature_header: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Mock Razorpay signature verification.
        
        Accepts any non-empty signature with sufficient length.
        """
        try:
            if not signature_header or len(signature_header) < 32:
                return False, "Invalid or empty signature"
            
            logger.info("MOCK: Razorpay signature verified")
            return True, None
        
        except Exception as e:
            return False, f"Mock verification error: {str(e)}"
    
    def generate_mock_stripe_signature(self, timestamp: Optional[int] = None) -> str:
        """
        Generate a mock Stripe signature for testing.
        
        Args:
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            Mock signature string in Stripe format
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # Generate a fake signature (64 hex chars)
        mock_signature = hashlib.sha256(f"mock_stripe_{timestamp}".encode()).hexdigest()
        
        return f"t={timestamp},v1={mock_signature}"
    
    def generate_mock_razorpay_signature(self) -> str:
        """
        Generate a mock Razorpay signature for testing.
        
        Returns:
            Mock signature string (64 hex chars)
        """
        return hashlib.sha256(f"mock_razorpay_{int(time.time())}".encode()).hexdigest()
