from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScaleRule:
    field: str
    factor: float
    offset: float = 0.0

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("ScaleRule field must not be empty")
        if self.factor == 0:
            raise ValueError("ScaleRule factor must not be zero")

    def apply(self, value: float) -> float:
        return value * self.factor + self.offset


def parse_scale_rules(spec: Optional[str]) -> list[ScaleRule]:
    """Parse a comma-separated list of field:factor[:offset] tokens.

    Example: 'latency:1000,score:0.01:5'
    """
    if not spec or not spec.strip():
        return []
    rules: list[ScaleRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid scale rule token: {token!r}")
        field_name = parts[0].strip()
        try:
            factor = float(parts[1])
        except ValueError:
            raise ValueError(f"Invalid factor in scale rule: {token!r}")
        offset = 0.0
        if len(parts) >= 3:
            try:
                offset = float(parts[2])
            except ValueError:
                raise ValueError(f"Invalid offset in scale rule: {token!r}")
        rules.append(ScaleRule(field=field_name, factor=factor, offset=offset))
    return rules


def scale_json_fields(data: dict, rules: list[ScaleRule]) -> dict:
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            try:
                result[rule.field] = rule.apply(float(result[rule.field]))
            except (TypeError, ValueError):
                pass
    return result


def scale_line(raw: str, rules: list[ScaleRule]) -> str:
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(scale_json_fields(data, rules))
