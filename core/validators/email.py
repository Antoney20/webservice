# core/validators.py

import re
from django.core.exceptions import ValidationError



MIN_LENGTH   = 6
MAX_LENGTH   = 254  # RFC 5321
MAX_LOCAL    = 64   # RFC 5321 local part


_LOCAL_RE = re.compile(r'^[a-zA-Z0-9]+([._\-][a-zA-Z0-9]+)*$')

# Consecutive or excessive dots in local part (a.s.d.f.r style)
_DOTSPAM_RE = re.compile(r'([a-zA-Z0-9]\.){3,}')  # 3+ x.x.x pattern


DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "trashmail.com",
    "10minutemail.com", "yopmail.com", "tempmail.com",
    "throwam.com", "sharklasers.com", "dispostable.com",
}


def validate_email_address(email: str) -> str:
    """
    Validates and normalises an email address.
    Raises ValidationError with a user-facing message on failure.
    Returns the cleaned lowercase email on success.
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Please provide a valid email address.")

    email = email.strip().lower()

    if len(email) < MIN_LENGTH or len(email) > MAX_LENGTH:
        raise ValidationError("Please provide a valid email address.")

    if email.count("@") != 1:
        raise ValidationError("Please provide a valid email address.")

    local, domain = email.split("@")

    if len(local) > MAX_LOCAL or len(local) < 1:
        raise ValidationError("Please provide a valid email address.")

    # Special characters in local part
    if not _LOCAL_RE.match(local):
        raise ValidationError("Please provide a valid email address.")

    # Dot-spam: a.s.d.f.r.g@... pattern
    if _DOTSPAM_RE.search(local):
        raise ValidationError("Please provide a valid email address.")

    # Domain structure
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or any(len(p) < 1 for p in domain_parts):
        raise ValidationError("Please provide a valid email address.")

    tld = domain_parts[-1]
    if len(tld) < 2 or not tld.isalpha():
        raise ValidationError("Please provide a valid email address.")

    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError("Please provide a valid email address.")

    return email