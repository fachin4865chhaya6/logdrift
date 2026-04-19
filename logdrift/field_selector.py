from __future__ import annotations

from typing import Optional


def parse_field_selector(raw: Optional[str]) -> list[str]:
    """Parse a comma-separated field selector string.

    Args:
        raw: e.g. "level,message,timestamp" or None.

    Returns:
        List of field name strings, empty if none.
    """
    if not raw or not raw.strip():
        return []
    return [f.strip() for f in raw.split(",") if f.strip()]


def select_fields(parsed: dict, fields: list[str]) -> dict:
    """Return a new dict containing only the requested fields.

    Fields that are absent in *parsed* are silently omitted.

    Args:
        parsed: The parsed JSON log object.
        fields: Field names to keep.

    Returns:
        Filtered dict.
    """
    if not fields:
        return parsed
    return {k: v for k, v in parsed.items() if k in fields}


def select_line(raw: str, parsed: Optional[dict], fields: list[str]) -> tuple[str, Optional[dict]]:
    """Apply field selection to a line.

    Args:
        raw: Original raw line.
        parsed: Parsed JSON dict or None.
        fields: Fields to keep.

    Returns:
        Tuple of (possibly modified raw, possibly modified parsed).
    """
    if not fields or parsed is None:
        return raw, parsed
    filtered = select_fields(parsed, fields)
    import json
    return json.dumps(filtered, separators=(",", ":")), filtered
