"""Field compactor: drop specified keys from JSON log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from logdrift.parser import parse_line


def parse_compact_fields(spec: str | None) -> list[str]:
    """Parse a comma-separated list of field names to drop."""
    if not spec:
        return []
    return [f.strip() for f in spec.split(",") if f.strip()]


def compact_json_fields(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Return a copy of *data* with *fields* removed."""
    return {k: v for k, v in data.items() if k not in fields}


def compact_line(raw: str, fields: list[str]) -> str:
    """Drop *fields* from a JSON log line and return the serialised result.

    Plain-text lines are returned unchanged.
    """
    if not fields:
        return raw
    data = parse_line(raw)
    if data is None:
        return raw
    import json
    return json.dumps(compact_json_fields(data, fields))
