"""Field formatter: apply sprintf-style format strings to JSON field values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from logdrift.parser import parse_line


@dataclass
class FormatRule:
    field: str
    fmt: str  # e.g. "{:.2f}" or "{:>10}"

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("FormatRule.field must not be empty")
        if not self.fmt.strip():
            raise ValueError("FormatRule.fmt must not be empty")

    def apply(self, value: Any) -> str:
        try:
            return self.fmt.format(value)
        except (ValueError, TypeError, KeyError):
            return str(value)


def parse_format_rules(spec: str | None) -> list[FormatRule]:
    """Parse 'field:fmt,field:fmt' into FormatRule objects.

    The separator between field and format string is the first colon.
    Example: ``latency:{:.3f},user:{:>12}``
    """
    if not spec:
        return []
    rules: list[FormatRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        idx = token.index(":")  # raises ValueError if missing
        field = token[:idx].strip()
        fmt = token[idx + 1:].strip()
        rules.append(FormatRule(field=field, fmt=fmt))
    return rules


def format_json_fields(data: dict, rules: list[FormatRule]) -> dict:
    """Return a copy of *data* with each matching field value reformatted."""
    if not rules:
        return data
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def format_line(raw: str, rules: list[FormatRule]) -> str:
    """Apply format rules to a raw log line.  Non-JSON lines are returned unchanged."""
    if not rules:
        return raw
    data = parse_line(raw)
    if data is None:
        return raw
    import json
    return json.dumps(format_json_fields(data, rules))
