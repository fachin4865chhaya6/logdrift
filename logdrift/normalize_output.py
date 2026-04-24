"""Thin output-layer helpers for the normalizer feature."""
from __future__ import annotations

from logdrift.normalizer import NormalizeRule, parse_normalize_rules, normalize_line


def make_normalize_rules(spec: str | None) -> list[NormalizeRule]:
    """Return a list of :class:`NormalizeRule` objects from *spec*, or ``[]``."""
    return parse_normalize_rules(spec)


def apply_normalization(raw: str, rules: list[NormalizeRule]) -> str:
    """Return *raw* with all *rules* applied, or *raw* unchanged when *rules* is empty."""
    if not rules:
        return raw
    return normalize_line(raw, rules)
