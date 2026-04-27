"""Output helpers for the stringer module."""
from __future__ import annotations

from logdrift.stringer import StringRule, parse_string_rules, string_line


def make_string_rules(spec: str | None) -> list[StringRule]:
    """Return a list of StringRule objects parsed from *spec*, or an empty list."""
    return parse_string_rules(spec)


def apply_string_ops_to_line(raw: str, rules: list[StringRule]) -> str:
    """Apply *rules* to *raw*, returning the transformed line.

    If *rules* is empty or the line is not valid JSON the original line is
    returned unchanged.
    """
    if not rules:
        return raw
    return string_line(raw, rules)
