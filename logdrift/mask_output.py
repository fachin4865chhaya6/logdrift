"""Integration helpers for field masking in the output pipeline."""
from __future__ import annotations

from logdrift.masker import MaskRule, parse_mask_rules, mask_line


def make_mask_rules(spec: str | None) -> list[MaskRule]:
    """Return a list of MaskRule objects from a CLI spec string, or empty list."""
    return parse_mask_rules(spec)


def apply_masking(line: str, rules: list[MaskRule]) -> str:
    """Apply masking rules to a line, returning the (possibly modified) line."""
    if not rules:
        return line
    return mask_line(line, rules)
