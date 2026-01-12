"""
Production Monitoring Integration
Includes Sentry for error tracking and performance monitoring
"""
import os
import logging
from typing import Optional
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger("monitoring")


def init_sentry():
    """
    Initialize Sentry for error tracking and performance monitoring
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured - monitoring disabled")
        return

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            integrations=[
                FastApiIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                ),
            ],
            before_send=before_send_sentry,
            before_send_transaction=before_send_transaction,
        )
        logger.info(f"Sentry initialized for environment: {environment}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_sentry(event, hint):
    """
    Filter sensitive data before sending to Sentry
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[Filtered]'

    # Remove sensitive data from extra context
    if 'extra' in event:
        sensitive_keys = ['password', 'token', 'secret', 'api_key']
        for key in list(event['extra'].keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                event['extra'][key] = '[Filtered]'

    return event


def before_send_transaction(event, hint):
    """
    Filter transactions before sending to Sentry
    Sample only important transactions to reduce costs
    """
    # Don't sample health check transactions
    if 'request' in event and 'url' in event['request']:
        url = event['request']['url']
        if '/health' in url or '/metrics' in url:
            return None

    return event


def capture_exception(exception: Exception, context: Optional[dict] = None):
    """
    Capture exception with optional context
    """
    try:
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(exception)
        else:
            sentry_sdk.capture_exception(exception)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message(message: str, level: str = "info", context: Optional[dict] = None):
    """
    Capture message with optional context
    """
    try:
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_message(message, level=level)
        else:
            sentry_sdk.capture_message(message, level=level)
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def set_user_context(user_id: str, email: Optional[str] = None):
    """
    Set user context for Sentry events
    """
    try:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email
        })
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def set_tag(key: str, value: str):
    """
    Set custom tag for Sentry events
    """
    try:
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.error(f"Failed to set tag in Sentry: {e}")


def start_transaction(name: str, op: str = "http.server"):
    """
    Start a performance transaction
    """
    try:
        return sentry_sdk.start_transaction(name=name, op=op)
    except Exception as e:
        logger.error(f"Failed to start transaction in Sentry: {e}")
        return None
