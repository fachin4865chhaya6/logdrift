"""Field extraction: pull values from JSON lines into new top-level keys."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractRule:
    source: str   # dot-separated JSON path, e.g. "meta.request.method"
    dest: str     # new top-level key name

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("ExtractRule.source must not be empty")
        if not self.dest.strip():
            raise ValueError("ExtractRule.dest must not be empty")

    def resolve(self, data: dict[str, Any]) -> Any:
        """Walk dot-path and return value, or None if missing."""
        parts = self.source.split(".")
        cur: Any = data
        for p in parts:
            if not isinstance(cur, dict) or p not in cur:
                return None
            cur = cur[p]
        return cur


def parse_extract_rules(spec: str | None) -> list[ExtractRule]:
    """Parse 'source:dest,...' spec into ExtractRule list."""
    if not spec:
        return []
    rules: list[ExtractRule] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise ValueError(f"Invalid extract rule (missing ':'): {token!r}")
        source, dest = token.split(":", 1)
        rules.append(ExtractRule(source=source.strip(), dest=dest.strip()))
    return rules


def extract_json_fields(data: dict[str, Any], rules: list[ExtractRule]) -> dict[str, Any]:
    """Return a copy of *data* with extracted fields injected at top level."""
    result = dict(data)
    for rule in rules:
        value = rule.resolve(data)
        if value is not None:
            result[rule.dest] = value
    return result


def extract_line(line: str, rules: list[ExtractRule]) -> str:
    """Apply extraction rules to a raw log line.  Non-JSON lines pass through."""
    if not rules:
        return line
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    if not isinstance(data, dict):
        return line
    return json.dumps(extract_json_fields(data, rules))
