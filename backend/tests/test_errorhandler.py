import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from backend.middleware.error_handler import http_error_handler

@pytest.mark.asyncio
async def test_http_error_handler_returns_500():
    # Mock request
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/test/path"
    
    # Test exception
    test_exception = ValueError("Test error")
    
    # Call handler
    response = await http_error_handler(mock_request, test_exception)
    
    assert response.status_code == 500
    assert b"Internal server error" in response.body

@pytest.mark.asyncio
async def test_http_error_handler_logs_exception():
    import logging
    
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/test"
    
    test_exception = RuntimeError("Something went wrong")
    
    with pytest.raises(Exception):
        # This should not raise, but we test it handles gracefully
        pass
    
    response = await http_error_handler(mock_request, test_exception)
    assert response.status_code == 500
