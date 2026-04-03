"""
Tests for OTP service and user settings API.
Parts D and C of the implementation plan.
"""
import pytest
import time
import os

os.environ.setdefault("ENVIRONMENT", "development")


class TestOTPService:
    """Tests for OTPService (dev mode)"""

    def test_generate_otp_is_6_digits(self):
        from backend.services.tb_otp_service import OTPService
        otp = OTPService.generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_is_different_each_time(self):
        from backend.services.tb_otp_service import OTPService
        otps = {OTPService.generate_otp() for _ in range(20)}
        assert len(otps) > 1

    @pytest.mark.asyncio
    async def test_send_otp_returns_dev_otp_in_dev_mode(self):
        from backend.services.tb_otp_service import OTPService
        result = await OTPService.send_otp("+919999999999", purpose="login")
        assert result["success"] is True
        # The service no longer returns plaintext OTPs in responses
        assert "dev_otp" not in result

    @pytest.mark.asyncio
    async def test_send_email_otp_returns_dev_otp_in_dev_mode(self):
        from backend.services.tb_otp_service import OTPService
        result = await OTPService.send_email_otp("test@example.com", purpose="login")
        assert result["success"] is True
        # Production behavior: plaintext OTP is not returned to callers
        assert "dev_otp" not in result

    @pytest.mark.asyncio
    async def test_verify_otp_success(self):
        from backend.services.tb_otp_service import OTPService, otp_store
        phone = "+911234567890"
        send_result = await OTPService.send_otp(phone, purpose="login")
        otp_code = send_result["dev_otp"]
        result = await OTPService.verify_otp(phone, otp_code, purpose="login")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_code_fails(self):
        from backend.services.tb_otp_service import OTPService
        from fastapi import HTTPException
        phone = "+910000000001"
        await OTPService.send_otp(phone, purpose="login")
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp(phone, "000000", purpose="login")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_expired_otp_fails(self):
        from backend.services.tb_otp_service import OTPService, otp_store
        from fastapi import HTTPException
        phone = "+910000000002"
        await OTPService.send_otp(phone, purpose="test")
        # Manually expire the OTP
        otp_store[phone]["expires_at"] = time.time() - 1
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp(phone, otp_store[phone]["otp"], purpose="test")
        assert exc_info.value.status_code == 400


class TestPrivacyLocation:
    """Tests for privacy location utilities"""

    def test_reduce_precision_rounds_to_3_decimals(self):
        from backend.services.tb_location_service import PrivacyLocation
        lat, lng = PrivacyLocation.reduce_precision(12.97162345, 77.59463210)
        assert lat == round(12.97162345, 3)
        assert lng == round(77.59463210, 3)

    def test_bucket_distance_rounds_up(self):
        from backend.services.tb_location_service import PrivacyLocation
        assert PrivacyLocation.bucket_distance(0.5) == 1.0
        assert PrivacyLocation.bucket_distance(1.1) == 2.0
        assert PrivacyLocation.bucket_distance(3.0) == 3.0

    def test_format_distance_display(self):
        from backend.services.tb_location_service import PrivacyLocation
        assert PrivacyLocation.format_distance_display(0.3) == "< 1 km"
        assert PrivacyLocation.format_distance_display(3.0) == "~3 km"
        assert PrivacyLocation.format_distance_display(7.0) == "< 10 km"
        assert PrivacyLocation.format_distance_display(20.0) == "< 25 km"
        assert PrivacyLocation.format_distance_display(60.0) == "~60 km"

    def test_is_location_fresh_within_ttl(self):
        from backend.services.tb_location_service import PrivacyLocation
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        recent = now - timedelta(seconds=300)
        assert PrivacyLocation.is_location_fresh(recent, ttl_seconds=900) is True

    def test_is_location_fresh_expired(self):
        from backend.services.tb_location_service import PrivacyLocation
        from datetime import datetime, timezone, timedelta
        old = datetime.now(timezone.utc) - timedelta(seconds=1000)
        assert PrivacyLocation.is_location_fresh(old, ttl_seconds=900) is False

    def test_calculate_distance_same_point(self):
        from backend.services.tb_location_service import PrivacyLocation
        dist = PrivacyLocation.calculate_distance(12.9716, 77.5946, 12.9716, 77.5946)
        assert dist == pytest.approx(0.0, abs=0.001)

    def test_calculate_distance_known_points(self):
        from backend.services.tb_location_service import PrivacyLocation
        # Bangalore to Mumbai is roughly 845 km by straight line
        dist = PrivacyLocation.calculate_distance(12.9716, 77.5946, 19.0760, 72.8777)
        assert 800 < dist < 950
