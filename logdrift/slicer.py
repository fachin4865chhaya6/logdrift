"""Field slicer: extract a substring or sub-list from JSON field values."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class SliceRule:
    """Describes how to slice a single field."""

    field: str
    start: Optional[int]
    stop: Optional[int]
    step: Optional[int]

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("SliceRule field must not be empty")
        self.field = self.field.strip()

    def apply(self, value: Any) -> Any:
        """Apply the slice to *value* if it supports slicing; return it unchanged otherwise."""
        if isinstance(value, (str, list)):
            return value[self.start : self.stop : self.step]
        return value


def parse_slice_rules(spec: Optional[str]) -> List[SliceRule]:
    """Parse a comma-separated list of slice specs.

    Each spec has the form::

        field:start:stop[:step]

    Any component except *field* may be omitted (empty string → ``None``).

    Examples::

        "message:0:100"          # first 100 chars of message
        "tags:1:5,name:0:8:2"   # two rules
    """
    if not spec or not spec.strip():
        return []

    rules: List[SliceRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        segments = part.split(":")
        if len(segments) < 3:
            raise ValueError(
                f"Slice spec '{part}' must have at least field:start:stop"
            )
        field = segments[0].strip()
        start = int(segments[1]) if segments[1].strip() else None
        stop = int(segments[2]) if segments[2].strip() else None
        step = int(segments[3]) if len(segments) > 3 and segments[3].strip() else None
        rules.append(SliceRule(field=field, start=start, stop=stop, step=step))
    return rules


def slice_json_fields(data: dict, rules: List[SliceRule]) -> dict:
    """Return a copy of *data* with slice rules applied."""
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def slice_line(raw: str, rules: List[SliceRule]) -> str:
    """Apply *rules* to *raw* if it is a JSON object; return *raw* unchanged otherwise."""
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(slice_json_fields(data, rules))
