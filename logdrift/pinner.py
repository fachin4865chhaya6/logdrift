"""Field pinning: always include specified fields at the top of formatted JSON output."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


def parse_pin_fields(spec: Optional[str]) -> list[str]:
    """Parse a comma-separated list of field names to pin."""
    if not spec or not spec.strip():
        return []
    return [f.strip() for f in spec.split(",") if f.strip()]


@dataclass
class FieldPinner:
    pin_fields: list[str]

    def __post_init__(self) -> None:
        if not self.pin_fields:
            raise ValueError("pin_fields must not be empty")

    def reorder(self, data: dict) -> dict:
        """Return a new dict with pinned fields first, preserving remaining order."""
        result: dict = {}
        for key in self.pin_fields:
            if key in data:
                result[key] = data[key]
        for key, value in data.items():
            if key not in result:
                result[key] = value
        return result


def pin_json_fields(line: str, pinner: FieldPinner) -> str:
    """Reorder JSON fields so pinned fields appear first; return line unchanged if not JSON."""
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    if not isinstance(data, dict):
        return line
    return json.dumps(pinner.reorder(data))


def pin_line(raw: str, pinner: Optional[FieldPinner]) -> str:
    """Apply field pinning to a raw log line if a pinner is configured."""
    if pinner is None:
        return raw
    return pin_json_fields(raw, pinner)
