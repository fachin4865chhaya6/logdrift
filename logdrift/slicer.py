from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json


@dataclass
class SliceRule:
    field: str
    start: int | None
    stop: int | None

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("field must not be empty")
        if self.start is None and self.stop is None:
            raise ValueError("at least one of start or stop must be set")

    def apply(self, value: Any) -> Any:
        if not isinstance(value, (str, list)):
            return value
        return value[self.start:self.stop]


def parse_slice_rules(spec: str | None) -> list[SliceRule]:
    if not spec:
        return []
    rules: list[SliceRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"invalid slice spec (missing ':'): {part!r}")
        field_part, slice_part = part.split(":", 1)
        field_part = field_part.strip()
        if not field_part:
            raise ValueError(f"empty field in slice spec: {part!r}")
        if ".." in slice_part:
            start_s, stop_s = slice_part.split("..", 1)
        else:
            start_s, stop_s = slice_part, ""
        start = int(start_s) if start_s.strip() else None
        stop = int(stop_s) if stop_s.strip() else None
        rules.append(SliceRule(field=field_part, start=start, stop=stop))
    return rules


def slice_json_fields(data: dict, rules: list[SliceRule]) -> dict:
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def slice_line(raw: str, rules: list[SliceRule]) -> str:
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(slice_json_fields(data, rules))
