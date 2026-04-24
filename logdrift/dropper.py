"""Field dropper: remove specified fields from JSON log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from logdrift.parser import parse_line


def parse_drop_fields(spec: str | None) -> list[str]:
    """Parse a comma-separated list of field names to drop.

    Args:
        spec: Comma-separated field names, or None / empty string.

    Returns:
        List of non-empty, stripped field name strings.
    """
    if not spec:
        return []
    return [f.strip() for f in spec.split(",") if f.strip()]


def drop_json_fields(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Return a copy of *data* with the given keys removed.

    Args:
        data:   Parsed JSON object.
        fields: Field names to remove.

    Returns:
        New dict without the dropped fields.
    """
    return {k: v for k, v in data.items() if k not in fields}


def drop_line(raw: str, fields: list[str]) -> str:
    """Remove *fields* from a JSON log line.

    If *raw* is not a valid JSON object or *fields* is empty, the original
    line is returned unchanged.

    Args:
        raw:    Raw log line string.
        fields: Field names to drop.

    Returns:
        Possibly modified JSON string, or the original *raw* value.
    """
    if not fields:
        return raw

    import json

    data = parse_line(raw)
    if data is None:
        return raw

    trimmed = drop_json_fields(data, fields)
    return json.dumps(trimmed)
