"""Field value capper: clamps numeric JSON fields to a min/max range."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class CapRule:
    field: str
    min_val: Optional[float]
    max_val: Optional[float]

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("CapRule field must not be empty")
        if self.min_val is None and self.max_val is None:
            raise ValueError("CapRule must specify at least one of min or max")
        if self.min_val is not None and self.max_val is not None:
            if self.min_val > self.max_val:
                raise ValueError("CapRule min_val must be <= max_val")

    def apply(self, value: float) -> float:
        result = value
        if self.min_val is not None:
            result = max(self.min_val, result)
        if self.max_val is not None:
            result = min(self.max_val, result)
        return result


def parse_cap_rules(spec: Optional[str]) -> list[CapRule]:
    """Parse 'field:min:max' comma-separated specs. Use '*' to omit a bound."""
    if not spec or not spec.strip():
        return []
    rules: list[CapRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        segments = part.split(":")
        if len(segments) != 3:
            raise ValueError(f"Invalid cap rule (expected field:min:max): {part!r}")
        field, raw_min, raw_max = segments
        min_val = None if raw_min.strip() == "*" else float(raw_min.strip())
        max_val = None if raw_max.strip() == "*" else float(raw_max.strip())
        rules.append(CapRule(field=field.strip(), min_val=min_val, max_val=max_val))
    return rules


def cap_json_fields(data: dict, rules: list[CapRule]) -> dict:
    result = dict(data)
    for rule in rules:
        if rule.field in result and isinstance(result[rule.field], (int, float)):
            result[rule.field] = rule.apply(result[rule.field])
    return result


def cap_line(raw: str, rules: list[CapRule]) -> str:
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(cap_json_fields(data, rules))
