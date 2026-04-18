"""Field value mapper — replaces field values based on a lookup table."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from logdrift.parser import parse_line


@dataclass
class FieldMapper:
    field: str
    mapping: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("field must not be empty")
        if not isinstance(self.mapping, dict):
            raise TypeError("mapping must be a dict")

    def apply(self, data: dict) -> dict:
        out = dict(data)
        if self.field in out:
            key = str(out[self.field])
            if key in self.mapping:
                out[self.field] = self.mapping[key]
        return out


def parse_mapper_spec(spec: str | None) -> list[FieldMapper]:
    """Parse 'field:json_object' pairs separated by semicolons.

    Example: 'level:{"info":"INFO","warn":"WARN"};env:{"prod":"production"}'
    """
    if not spec or not spec.strip():
        return []
    mappers: list[FieldMapper] = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        colon = part.index(":")
        fname = part[:colon].strip()
        raw = part[colon + 1:].strip()
        mapping = json.loads(raw)
        mappers.append(FieldMapper(field=fname, mapping=mapping))
    return mappers


def map_json_fields(data: dict, mappers: list[FieldMapper]) -> dict:
    for m in mappers:
        data = m.apply(data)
    return data


def map_line(line: str, mappers: list[FieldMapper]) -> str:
    if not mappers:
        return line
    data = parse_line(line)
    if data is None:
        return line
    return json.dumps(map_json_fields(data, mappers))
