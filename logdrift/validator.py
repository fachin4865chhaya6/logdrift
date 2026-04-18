from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import re
from logdrift.parser import parse_line, get_json_path_value


@dataclass
class ValidationRule:
    json_path: str
    pattern: str
    tag: str = "invalid"
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.json_path.strip():
            raise ValueError("json_path must not be empty")
        if not self.pattern.strip():
            raise ValueError("pattern must not be empty")
        self._compiled = re.compile(self.pattern)

    def validate(self, data: dict[str, Any]) -> bool:
        value = get_json_path_value(data, self.json_path)
        if value is None:
            return False
        return bool(self._compiled.search(str(value)))


def parse_validation_rules(spec: str | None) -> list[ValidationRule]:
    """Parse 'path:pattern:tag,...' spec into ValidationRule list."""
    if not spec:
        return []
    rules: list[ValidationRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        segments = part.split(":")
        if len(segments) < 2:
            raise ValueError(f"Invalid validation rule: {part!r}")
        json_path = segments[0].strip()
        pattern = segments[1].strip()
        tag = segments[2].strip() if len(segments) >= 3 else "invalid"
        rules.append(ValidationRule(json_path=json_path, pattern=pattern, tag=tag))
    return rules


def validate_line(raw: str, rules: list[ValidationRule]) -> tuple[str, list[str]]:
    """Return (raw, failed_tags). If no rules or not JSON, returns (raw, [])."""
    if not rules:
        return raw, []
    data = parse_line(raw)
    if data is None:
        return raw, []
    failed = [r.tag for r in rules if not r.validate(data)]
    return raw, failed
