"""Output helpers for field formatting."""
from __future__ import annotations

from logdrift.formatter_field import FormatRule, parse_format_rules, format_line


def make_format_rules(spec: str | None) -> list[FormatRule]:
    """Return a list of FormatRule objects from CLI spec, or empty list."""
    return parse_format_rules(spec)


def apply_formatting(raw: str, rules: list[FormatRule]) -> str:
    """Apply format rules to *raw*.  Returns the original string when no rules exist."""
    if not rules:
        return raw
    return format_line(raw, rules)
