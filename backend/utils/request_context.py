from contextvars import ContextVar
from typing import Optional
from uuid import uuid4

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


def set_request_id(request_id: str = None) -> str:
    """Set request ID for current context"""
    if request_id is None:
        request_id = str(uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get request ID from current context"""
    return request_id_var.get()


def set_user_id(user_id: str):
    """Set user ID for current context"""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get user ID from current context"""
    return user_id_var.get()


def clear_context():
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)
