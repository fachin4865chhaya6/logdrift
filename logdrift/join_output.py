"""Output helpers for the field joiner."""
from __future__ import annotations

from logdrift.joiner import JoinRule, parse_join_rules, join_line


def make_join_rules(spec: str | None) -> list[JoinRule]:
    """Return a list of JoinRule objects parsed from *spec*, or empty list."""
    return parse_join_rules(spec)


def apply_joining(raw: str, rules: list[JoinRule]) -> str:
    """Apply *rules* to *raw* and return the transformed line."""
    if not rules:
        return raw
    return join_line(raw, rules)
