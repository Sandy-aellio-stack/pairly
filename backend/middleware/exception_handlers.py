"""
Comprehensive Exception Handlers for FastAPI
Provides consistent error responses across the application
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

logger = logging.getLogger("exception_handler")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTPException with consistent format
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with user-friendly messages
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append({
            "field": field,
            "message": message,
            "type": error["type"]
        })

    logger.warning(
        f"Validation error: {len(errors)} field(s) invalid",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": 422,
            "details": errors,
            "path": request.url.path
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions
    Never expose stack traces in production
    """
    # Log full exception with stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )

    # Production: generic message
    if ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An unexpected error occurred",
                "status_code": 500,
                "path": request.url.path
            }
        )

    # Development: detailed error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    )


def setup_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
