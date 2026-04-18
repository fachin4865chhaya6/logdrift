"""Thin output helpers for the extractor feature."""
from __future__ import annotations

from logdrift.extractor import ExtractRule, parse_extract_rules, extract_line


def make_extract_rules(spec: str | None) -> list[ExtractRule]:
    """Return rules parsed from *spec*, or an empty list."""
    return parse_extract_rules(spec)


def apply_extraction(line: str, rules: list[ExtractRule]) -> str:
    """Return *line* after applying *rules* (pass-through when rules is empty)."""
    if not rules:
        return line
    return extract_line(line, rules)
