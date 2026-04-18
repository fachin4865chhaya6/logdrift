from __future__ import annotations

import json
from typing import Optional


def parse_rename_map(spec: Optional[str]) -> dict[str, str]:
    """Parse 'old:new,old2:new2' into a dict."""
    if not spec:
        return {}
    result = {}
    for pair in spec.split(","):
        pair = pair.strip()
        if ":" not in pair:
            raise ValueError(f"Invalid rename pair (expected old:new): {pair!r}")
        old, new = pair.split(":", 1)
        old, new = old.strip(), new.strip()
        if not old or not new:
            raise ValueError(f"Rename pair keys must be non-empty: {pair!r}")
        result[old] = new
    return result


def rename_json_fields(data: dict, rename_map: dict[str, str]) -> dict:
    """Return a new dict with keys renamed according to rename_map."""
    result = {}
    for key, value in data.items():
        result[rename_map.get(key, key)] = value
    return result


def rename_line(line: str, rename_map: dict[str, str]) -> str:
    """Apply field renaming to a JSON log line; return line unchanged if not JSON."""
    if not rename_map:
        return line
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    if not isinstance(data, dict):
        return line
    return json.dumps(rename_json_fields(data, rename_map))
