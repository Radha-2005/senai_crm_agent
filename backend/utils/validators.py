"""
utils/validators.py - Input validation utilities.
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize text input by stripping dangerous characters."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace('\x00', '')
    # Limit length
    return text[:max_length]


def validate_email_id(email_id: str) -> bool:
    """Validate email ID format."""
    if not email_id:
        return False
    # Allow alphanumeric, underscore, hyphen
    return bool(re.match(r'^[a-zA-Z0-9_\-]{1,50}$', email_id))
