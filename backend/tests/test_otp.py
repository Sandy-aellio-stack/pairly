"""
Lightweight unit tests for OTP utilities.

These tests avoid relying on dev-only behaviors (no plaintext `dev_otp` returned).
They validate OTP generation and basic validation error handling.
"""

import pytest

from backend.services.tb_otp_service import OTPService
from fastapi import HTTPException


class TestGenerateOTP:
    def test_returns_six_digit_string(self):
        otp = OTPService.generate_otp()
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_values_are_in_valid_range(self):
        for _ in range(20):
            otp_val = int(OTPService.generate_otp())
            assert 100000 <= otp_val <= 999999


class TestSendOTPValidation:
    @pytest.mark.asyncio
    async def test_raises_on_missing_phone(self):
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.send_otp("", purpose="login")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_on_missing_email(self):
        with pytest.raises(HTTPException) as exc_info:
            await OTPService.send_email_otp("", purpose="login")
        assert exc_info.value.status_code == 400
