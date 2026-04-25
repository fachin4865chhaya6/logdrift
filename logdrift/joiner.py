"""Field joiner: concatenate multiple JSON fields into a new field."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JoinRule:
    sources: list[str]
    dest: str
    sep: str = " "

    def __post_init__(self) -> None:
        if not self.sources:
            raise ValueError("sources must not be empty")
        if not self.dest or not self.dest.strip():
            raise ValueError("dest must not be empty")

    def apply(self, data: dict[str, Any]) -> dict[str, Any]:
        parts = [str(data[k]) for k in self.sources if k in data]
        if parts:
            data[self.dest] = self.sep.join(parts)
        return data


def parse_join_rules(spec: str | None) -> list[JoinRule]:
    """Parse a semicolon-separated list of join specs.

    Each spec has the form: ``dest=src1,src2[|sep]``.
    Example: ``full_name=first,last| ``
    """
    if not spec or not spec.strip():
        return []
    rules: list[JoinRule] = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid join spec (missing '='): {part!r}")
        dest, rest = part.split("=", 1)
        dest = dest.strip()
        sep = " "
        if "|" in rest:
            rest, sep = rest.rsplit("|", 1)
        sources = [s.strip() for s in rest.split(",") if s.strip()]
        rules.append(JoinRule(sources=sources, dest=dest, sep=sep))
    return rules


def join_json_fields(data: dict[str, Any], rules: list[JoinRule]) -> dict[str, Any]:
    for rule in rules:
        data = rule.apply(data)
    return data


def join_line(raw: str, rules: list[JoinRule]) -> str:
    """Apply join rules to a raw log line, returning the (possibly modified) line."""
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(join_json_fields(data, rules))
