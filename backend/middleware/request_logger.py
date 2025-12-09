import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.utils.request_context import set_request_id, clear_context, get_request_id
from backend.utils.log_sanitizer import LogSanitizer

logger = logging.getLogger('api.request')


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Set request ID
        request_id = set_request_id()
        
        # Start timing
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else 'unknown'
        
        # Log request
        logger.info(
            'HTTP request started',
            extra={
                'event': 'http_request_start',
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'client_ip': client_ip,
                'user_agent': request.headers.get('user-agent', 'unknown')
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                'HTTP request completed',
                extra={
                    'event': 'http_request_complete',
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'client_ip': client_ip
                }
            )
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f'HTTP request failed: {str(e)}',
                extra={
                    'event': 'http_request_error',
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': round(duration_ms, 2),
                    'error': str(e)
                },
                exc_info=True
            )
            raise
        finally:
            clear_context()
