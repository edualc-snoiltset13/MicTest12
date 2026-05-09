import re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_PHONE_RE = re.compile(r'^\+?[\d\s\-().]{7,20}$')
_URL_RE = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)

_VALIDATORS = {
    "email": (_EMAIL_RE, "invalid email address"),
    "phone": (_PHONE_RE, "invalid phone number"),
    "url": (_URL_RE, "invalid URL"),
}


def _validate_email(value):
    return None if _EMAIL_RE.match(value) else "invalid email address"


def _validate_phone(value):
    return None if _PHONE_RE.match(value) else "invalid phone number"


def _validate_url(value):
    return None if _URL_RE.match(value) else "invalid URL"


def validate(payload, schema):
    """Validate form data against a schema; returns {"valid": bool, "errors": {field: [msg]}}."""
    errors = {}
    for field, validator_type in schema.items():
        if validator_type not in _VALIDATORS:
            raise ValueError(f"unknown validator type: {validator_type!r}")
        value = payload.get(field)
        if value is None:
            errors.setdefault(field, []).append("field is required")
            continue
        pattern, msg = _VALIDATORS[validator_type]
        if not pattern.match(str(value)):
            errors.setdefault(field, []).append(msg)
    return {"valid": not errors, "errors": errors}
