import logging
from typing import Optional
import os

logger = logging.getLogger('location_detector')


class LocationDetector:
    """
    Service to detect user location and determine appropriate payment provider.

    For production, this should integrate with a proper IP geolocation service.
    For now, it uses request headers and IP-based detection.
    """

    @staticmethod
    async def detect_country_from_ip(ip_address: str) -> Optional[str]:
        """
        Detect country from IP address.

        In production, integrate with a geolocation API like:
        - MaxMind GeoIP2
        - IP2Location
        - ipapi.co

        For now, returns None (requires manual provider selection)
        """
        try:
            import requests
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
            if response.status_code == 200:
                data = response.json()
                country_code = data.get('countryCode', '').upper()
                logger.info(f"Detected country from IP {ip_address}: {country_code}")
                return country_code
        except Exception as e:
            logger.warning(f"Failed to detect country from IP {ip_address}: {e}")

        return None

    @staticmethod
    async def get_payment_provider_for_country(country_code: Optional[str]) -> str:
        """
        Determine appropriate payment provider based on country.

        Rules:
        - India (IN) -> Razorpay
        - All other countries -> Stripe
        - Unknown/None -> Stripe (default)
        """
        if country_code and country_code.upper() == 'IN':
            logger.info(f"Selected Razorpay provider for country: {country_code}")
            return 'razorpay'

        logger.info(f"Selected Stripe provider for country: {country_code or 'unknown'}")
        return 'stripe'

    @staticmethod
    async def get_payment_provider_for_user(
        ip_address: Optional[str] = None,
        user_country: Optional[str] = None,
        manual_provider: Optional[str] = None
    ) -> str:
        """
        Get payment provider for user based on multiple factors.

        Priority:
        1. Manual provider selection (if specified)
        2. User's stored country preference
        3. IP-based detection
        4. Default to Stripe
        """
        if manual_provider and manual_provider.lower() in ['stripe', 'razorpay']:
            logger.info(f"Using manual provider selection: {manual_provider}")
            return manual_provider.lower()

        if user_country:
            return await LocationDetector.get_payment_provider_for_country(user_country)

        if ip_address:
            detected_country = await LocationDetector.detect_country_from_ip(ip_address)
            if detected_country:
                return await LocationDetector.get_payment_provider_for_country(detected_country)

        logger.info("No location detected, defaulting to Stripe")
        return 'stripe'

    @staticmethod
    def get_currency_for_provider(provider: str) -> str:
        """
        Get default currency for payment provider.

        - Razorpay -> INR (Indian Rupee)
        - Stripe -> USD (US Dollar)
        """
        currency_map = {
            'razorpay': 'INR',
            'stripe': 'USD'
        }
        return currency_map.get(provider.lower(), 'USD')


_location_detector = LocationDetector()


def get_location_detector() -> LocationDetector:
    """Get global location detector instance"""
    return _location_detector
