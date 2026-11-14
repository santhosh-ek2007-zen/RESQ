"""
app/validation.py — Request payload validation helpers.

Returns (value, None) on success or (None, error_message) on failure.
"""
from __future__ import annotations


def require_json(request) -> tuple[dict | None, str | None]:
    """Return parsed JSON body or error message."""
    data = request.get_json(silent=True)
    if data is None:
        return None, "Request body must be valid JSON with Content-Type: application/json."
    return data, None


def require_string(data: dict, field: str) -> tuple[str | None, str | None]:
    """Extract a non-empty string field."""
    val = data.get(field)
    if not isinstance(val, str) or not val.strip():
        return None, f"Field '{field}' must be a non-empty string."
    return val.strip(), None


def require_list(data: dict, field: str, min_len: int = 0) -> tuple[list | None, str | None]:
    """Extract a list field with optional minimum length."""
    val = data.get(field)
    if not isinstance(val, list):
        return None, f"Field '{field}' must be a list."
    if len(val) < min_len:
        return None, f"Field '{field}' must have at least {min_len} element(s)."
    return val, None


def optional_int(data: dict, field: str, default: int) -> tuple[int, str | None]:
    """Extract an optional integer field with a default."""
    val = data.get(field, default)
    if not isinstance(val, int):
        try:
            val = int(val)
        except (TypeError, ValueError):
            return default, f"Field '{field}' must be an integer."
    return val, None


def optional_string(data: dict, field: str, default: str, choices: list[str] | None = None) -> tuple[str, str | None]:
    """Extract an optional string field with a default and optional allowed choices."""
    val = data.get(field, default)
    if not isinstance(val, str):
        return default, f"Field '{field}' must be a string."
    if choices and val not in choices:
        return default, f"Field '{field}' must be one of: {', '.join(choices)}."
    return val, None

