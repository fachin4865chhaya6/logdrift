"""Field transformer for remapping or dropping JSON log fields before output."""

from __future__ import annotations

import json
from typing import Any


def parse_field_map(raw: str | None) -> dict[str, str]:
    """Parse a comma-separated list of 'old=new' field rename specs.

    Returns a dict mapping original field names to their new names.
    A value of '' means the field should be dropped.

    Example:
        'msg=message,ts=timestamp' -> {'msg': 'message', 'ts': 'timestamp'}
        'debug=' -> {'debug': ''}  (drop 'debug')
    """
    if not raw:
        return {}
    result: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid field map entry (expected 'old=new'): {part!r}")
        old, new = part.split("=", 1)
        old = old.strip()
        new = new.strip()
        if not old:
            raise ValueError(f"Empty source field name in entry: {part!r}")
        result[old] = new
    return result


def transform_fields(data: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    """Apply a field map to a parsed JSON object.

    Fields whose mapped name is '' are dropped.
    Fields not in the map are left unchanged.
    """
    if not field_map:
        return data
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key not in field_map:
            result[key] = value
        else:
            new_key = field_map[key]
            if new_key:  # non-empty means rename
                result[new_key] = value
            # empty string means drop — skip the field
    return result


def transform_line(line: str, field_map: dict[str, str]) -> str:
    """Apply field transformations to a log line.

    If the line is valid JSON and field_map is non-empty, the transformed
    object is re-serialised and returned.  Otherwise the original line is
    returned unchanged.
    """
    if not field_map or not line.strip():
        return line
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return line
    if not isinstance(data, dict):
        return line
    transformed = transform_fields(data, field_map)
    return json.dumps(transformed)
