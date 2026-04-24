"""Field value normalizer: lowercase, strip whitespace, or apply case transforms."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json

_TRANSFORMS = {"lower", "upper", "strip", "title"}


@dataclass
class NormalizeRule:
    field: str
    transform: str

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("field must not be empty")
        if self.transform not in _TRANSFORMS:
            raise ValueError(
                f"unsupported transform {self.transform!r}; choose from {sorted(_TRANSFORMS)}"
            )

    def apply(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        if self.transform == "lower":
            return value.lower()
        if self.transform == "upper":
            return value.upper()
        if self.transform == "strip":
            return value.strip()
        if self.transform == "title":
            return value.title()
        return value  # pragma: no cover


def parse_normalize_rules(spec: str | None) -> list[NormalizeRule]:
    """Parse a comma-separated list of ``field:transform`` pairs.

    Example: ``"level:lower,message:strip"``
    """
    if not spec or not spec.strip():
        return []
    rules: list[NormalizeRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise ValueError(f"invalid normalize rule {token!r}; expected 'field:transform'")
        field, transform = token.split(":", 1)
        rules.append(NormalizeRule(field=field.strip(), transform=transform.strip()))
    return rules


def normalize_json_fields(data: dict, rules: list[NormalizeRule]) -> dict:
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def normalize_line(raw: str, rules: list[NormalizeRule]) -> str:
    """Apply normalization rules to a raw log line; returns the line unchanged if not JSON."""
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(normalize_json_fields(data, rules), separators=(",", ":"))
