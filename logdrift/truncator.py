"""Field truncation: trim long field values in JSON log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from logdrift.parser import parse_line


def parse_truncate_fields(spec: Optional[str]) -> dict[str, int]:
    """Parse 'field:maxlen,field2:maxlen2' into a dict."""
    if not spec:
        return {}
    result: dict[str, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            raise ValueError(f"Invalid truncate spec (missing ':'): {part!r}")
        name, _, length_str = part.partition(":")
        name = name.strip()
        length_str = length_str.strip()
        if not name:
            raise ValueError(f"Empty field name in truncate spec: {part!r}")
        try:
            length = int(length_str)
        except ValueError:
            raise ValueError(f"Non-integer max length in truncate spec: {part!r}")
        if length <= 0:
            raise ValueError(f"Max length must be positive, got {length}")
        result[name] = length
    return result


def truncate_json_fields(data: dict, fields: dict[str, int]) -> dict:
    """Return a copy of *data* with string values truncated to their limits."""
    out = dict(data)
    for field_name, max_len in fields.items():
        if field_name in out and isinstance(out[field_name], str):
            value = out[field_name]
            if len(value) > max_len:
                out[field_name] = value[:max_len] + "…"
    return out


def truncate_line(raw: str, fields: dict[str, int]) -> str:
    """Truncate fields in *raw* if it is a JSON object; otherwise return as-is."""
    if not fields:
        return raw
    data = parse_line(raw)
    if data is None:
        return raw
    return __import__("json").dumps(truncate_json_fields(data, fields))
