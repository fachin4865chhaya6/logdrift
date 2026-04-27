"""Field string-operation rules for logdrift.

Supports strip, lstrip, rstrip, upper, lower, title, replace, and prefix/suffix operations
on JSON string fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from logdrift.parser import parse_line

_SUPPORTED_OPS = {"strip", "lstrip", "rstrip", "upper", "lower", "title", "replace", "prefix", "suffix"}


@dataclass
class StringRule:
    field: str
    op: str
    arg: str = ""

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("field must not be empty")
        if self.op not in _SUPPORTED_OPS:
            raise ValueError(f"unsupported op '{self.op}'; choose from {sorted(_SUPPORTED_OPS)}")
        if self.op == "replace" and ":" not in self.arg:
            raise ValueError("replace arg must be 'old:new'")

    def apply(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        if self.op == "strip":
            return value.strip()
        if self.op == "lstrip":
            return value.lstrip()
        if self.op == "rstrip":
            return value.rstrip()
        if self.op == "upper":
            return value.upper()
        if self.op == "lower":
            return value.lower()
        if self.op == "title":
            return value.title()
        if self.op == "replace":
            old, new = self.arg.split(":", 1)
            return value.replace(old, new)
        if self.op == "prefix":
            return self.arg + value
        if self.op == "suffix":
            return value + self.arg
        return value  # pragma: no cover


def parse_string_rules(spec: str | None) -> list[StringRule]:
    """Parse a comma-separated list of 'field:op' or 'field:op:arg' tokens."""
    if not spec or not spec.strip():
        return []
    rules: list[StringRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split(":", 2)
        if len(parts) < 2:
            raise ValueError(f"invalid string rule token '{token}'; expected 'field:op' or 'field:op:arg'")
        field, op = parts[0].strip(), parts[1].strip()
        arg = parts[2].strip() if len(parts) == 3 else ""
        rules.append(StringRule(field=field, op=op, arg=arg))
    return rules


def apply_string_ops(data: dict, rules: list[StringRule]) -> dict:
    """Return a copy of *data* with each rule applied in order."""
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def string_line(raw: str, rules: list[StringRule]) -> str:
    """Apply string rules to a raw log line and return the (possibly modified) line."""
    if not rules:
        return raw
    data = parse_line(raw)
    if data is None:
        return raw
    import json
    return json.dumps(apply_string_ops(data, rules))
