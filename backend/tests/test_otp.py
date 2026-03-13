"""
Unit tests for the OTP service (tb_otp_service).

Covers:
- OTP generation (6 digits)
- send_otp stores and returns dev_otp
- verify_otp succeeds with correct code
- verify_otp raises on wrong code
- verify_otp raises on expired OTP
- verify_otp raises when OTP not found
- OTP is consumed after successful verification (cannot be reused)
- send_email_otp stores and returns dev_otp
- verify_email_otp works correctly
"""

import time
import pytest
from unittest.mock import patch, AsyncMock

from backend.services.tb_otp_service import OTPService, otp_store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_store(identifier: str):
    """Remove an identifier from the in-memory store if present."""
    otp_store.pop(identifier, None)


# ---------------------------------------------------------------------------
# generate_otp
# ---------------------------------------------------------------------------

class TestGenerateOTP:
    def test_returns_six_digit_string(self):
        otp = OTPService.generate_otp()
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_values_are_in_valid_range(self):
        for _ in range(20):
            otp = int(OTPService.generate_otp())
            assert 100000 <= otp <= 999999


# ---------------------------------------------------------------------------
# send_otp (SMS / mobile)
# ---------------------------------------------------------------------------

class TestSendOTP:
    @pytest.mark.asyncio
    async def test_returns_dev_otp_in_non_production(self):
        phone = "+919999000001"
        _clear_store(phone)
        result = await OTPService.send_otp(phone, purpose="login")
        assert result["success"] is True
        assert "dev_otp" in result
        assert len(result["dev_otp"]) == 6
        _clear_store(phone)

    @pytest.mark.asyncio
    async def test_stores_otp_in_memory(self):
        phone = "+919999000002"
        _clear_store(phone)
        result = await OTPService.send_otp(phone, purpose="login")
        assert phone in otp_store
        assert otp_store[phone]["otp"] == result["dev_otp"]
        _clear_store(phone)

    @pytest.mark.asyncio
    async def test_no_dev_otp_in_production(self):
        phone = "+919999000003"
        _clear_store(phone)
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            result = await OTPService.send_otp(phone, purpose="login")
        assert "dev_otp" not in result
        _clear_store(phone)

    @pytest.mark.asyncio
    async def test_raises_on_missing_phone(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.send_otp("", purpose="login")
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# verify_otp
# ---------------------------------------------------------------------------

class TestVerifyOTP:
    @pytest.mark.asyncio
    async def test_correct_otp_returns_true(self):
        phone = "+919999000010"
        result = await OTPService.send_otp(phone, purpose="login")
        otp_code = result["dev_otp"]
        verified = await OTPService.verify_otp(phone, otp_code, purpose="login")
        assert verified is True

    @pytest.mark.asyncio
    async def test_wrong_otp_raises_400(self):
        from fastapi import HTTPException
        phone = "+919999000011"
        await OTPService.send_otp(phone, purpose="login")
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp(phone, "000000", purpose="login")
        assert exc_info.value.status_code == 400
        _clear_store(phone)

    @pytest.mark.asyncio
    async def test_otp_is_consumed_after_use(self):
        from fastapi import HTTPException
        phone = "+919999000012"
        result = await OTPService.send_otp(phone, purpose="login")
        otp_code = result["dev_otp"]
        await OTPService.verify_otp(phone, otp_code, purpose="login")
        with pytest.raises(HTTPException):
            await OTPService.verify_otp(phone, otp_code, purpose="login")

    @pytest.mark.asyncio
    async def test_expired_otp_raises_400(self):
        from fastapi import HTTPException
        phone = "+919999000013"
        await OTPService.send_otp(phone, purpose="login")
        otp_store[phone]["expires_at"] = time.time() - 1
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp(phone, otp_store[phone]["otp"], purpose="login")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_not_found_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.verify_otp("+910000000000", "123456", purpose="login")
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# send_email_otp
# ---------------------------------------------------------------------------

class TestSendEmailOTP:
    @pytest.mark.asyncio
    async def test_returns_dev_otp(self):
        email = "testuser@example.com"
        _clear_store(email)
        with patch("backend.services.tb_otp_service.OTPService.send_otp", new_callable=AsyncMock):
            result = await OTPService.send_email_otp(email, purpose="login")
        assert "dev_otp" in result
        _clear_store(email)

    @pytest.mark.asyncio
    async def test_verify_email_otp_works(self):
        email = "verify@example.com"
        _clear_store(email)
        result = await OTPService.send_email_otp(email, purpose="login")
        otp_code = result["dev_otp"]
        verified = await OTPService.verify_email_otp(email, otp_code, purpose="login")
        assert verified is True

    @pytest.mark.asyncio
    async def test_raises_on_missing_email(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.send_email_otp("", purpose="login")
        assert exc_info.value.status_code == 400
