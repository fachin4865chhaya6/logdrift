"""Field value clipper: trims string field values to a maximum character length."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from logdrift.parser import parse_line


@dataclass
class ClipRule:
    field: str
    max_length: int
    suffix: str = "..."

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("ClipRule.field must not be empty")
        if self.max_length <= 0:
            raise ValueError("ClipRule.max_length must be a positive integer")

    def apply(self, value: Any) -> Any:
        """Clip a string value to max_length, appending suffix if truncated."""
        if not isinstance(value, str):
            return value
        if len(value) <= self.max_length:
            return value
        return value[: self.max_length] + self.suffix


def parse_clip_rules(spec: str | None) -> list[ClipRule]:
    """Parse a comma-separated spec like 'message:80,reason:40'.

    Each token is ``field:max_length`` with an optional ``:suffix`` third part.
    """
    if not spec or not spec.strip():
        return []
    rules: list[ClipRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split(":")
        if len(parts) < 2:
            raise ValueError(f"Invalid clip spec token (expected field:max_length): {token!r}")
        field = parts[0].strip()
        try:
            max_length = int(parts[1].strip())
        except ValueError:
            raise ValueError(f"max_length must be an integer in clip spec token: {token!r}")
        suffix = parts[2] if len(parts) >= 3 else "..."
        rules.append(ClipRule(field=field, max_length=max_length, suffix=suffix))
    return rules


def clip_json_fields(data: dict, rules: list[ClipRule]) -> dict:
    """Return a shallow copy of *data* with clip rules applied."""
    if not rules:
        return data
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def clip_line(raw: str, rules: list[ClipRule]) -> str:
    """Apply clip rules to a log line, returning the (possibly modified) line."""
    if not rules:
        return raw
    data = parse_line(raw)
    if data is None:
        return raw
    clipped = clip_json_fields(data, rules)
    import json
    return json.dumps(clipped, separators=(", ", ": "))
