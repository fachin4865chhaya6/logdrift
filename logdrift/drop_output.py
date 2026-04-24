"""Output helpers for the field-dropper feature."""
from __future__ import annotations

from logdrift.dropper import parse_drop_fields, drop_line


def make_drop_fields(spec: str | None) -> list[str]:
    """Parse *spec* into a list of field names to drop.

    Args:
        spec: Comma-separated field names or None.

    Returns:
        List of field name strings (may be empty).
    """
    return parse_drop_fields(spec)


def apply_drop(raw: str, fields: list[str]) -> str:
    """Apply field-dropping to *raw* using the pre-parsed *fields* list.

    Args:
        raw:    Raw log line.
        fields: Fields to remove (from :func:`make_drop_fields`).

    Returns:
        Transformed line, or *raw* if no fields or not JSON.
    """
    if not fields:
        return raw
    return drop_line(raw, fields)
