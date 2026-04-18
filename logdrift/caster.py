"""Field type casting for structured log lines."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
import json


@dataclass
class CastRule:
    field: str
    cast_type: str  # int, float, bool, str

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("field must not be empty")
        if self.cast_type not in ("int", "float", "bool", "str"):
            raise ValueError(f"unsupported cast type: {self.cast_type}")

    def apply(self, value: Any) -> Any:
        if self.cast_type == "int":
            return int(value)
        if self.cast_type == "float":
            return float(value)
        if self.cast_type == "bool":
            if isinstance(value, bool):
                return value
            return str(value).lower() not in ("false", "0", "", "no")
        return str(value)


def parse_cast_rules(spec: str | None) -> List[CastRule]:
    """Parse 'field:type,field:type' into CastRule list."""
    if not spec:
        return []
    rules: List[CastRule] = []
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            raise ValueError(f"invalid cast spec (expected field:type): {part}")
        field, cast_type = part.split(":", 1)
        rules.append(CastRule(field=field.strip(), cast_type=cast_type.strip()))
    return rules


def cast_json_fields(data: Dict[str, Any], rules: List[CastRule]) -> Dict[str, Any]:
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            try:
                result[rule.field] = rule.apply(result[rule.field])
            except (ValueError, TypeError):
                pass
    return result


def cast_line(line: str, rules: List[CastRule]) -> str:
    if not rules:
        return line
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return line
    if not isinstance(data, dict):
        return line
    return json.dumps(cast_json_fields(data, rules))
