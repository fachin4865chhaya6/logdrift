"""Flatten nested JSON fields into dot-notation keys."""
from __future__ import annotations

from typing import Any

from logdrift.parser import parse_line


def parse_flatten_depth(value: str | None) -> int:
    """Parse a max-depth string into an integer (0 = unlimited)."""
    if value is None:
        return 0
    try:
        depth = int(value)
    except ValueError:
        raise ValueError(f"Invalid flatten depth: {value!r}")
    if depth < 0:
        raise ValueError(f"Flatten depth must be >= 0, got {depth}")
    return depth


def _flatten(obj: Any, prefix: str, depth: int, max_depth: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(obj, dict) and (max_depth == 0 or depth < max_depth):
        for key, value in obj.items():
            flat_key = f"{prefix}.{key}" if prefix else key
            result.update(_flatten(value, flat_key, depth + 1, max_depth))
    else:
        result[prefix] = obj
    return result


def flatten_json(data: dict[str, Any], max_depth: int = 0) -> dict[str, Any]:
    """Return a new dict with nested keys flattened using dot notation."""
    return _flatten(data, "", 0, max_depth)


def flatten_line(raw: str, max_depth: int = 0) -> str:
    """Flatten a JSON log line; return the original string if not JSON."""
    data = parse_line(raw)
    if data is None:
        return raw
    import json
    return json.dumps(flatten_json(data, max_depth))
