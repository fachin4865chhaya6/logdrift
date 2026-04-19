from __future__ import annotations
from logdrift.slicer import parse_slice_rules, slice_line, SliceRule


def make_slice_rules(spec: str | None) -> list[SliceRule]:
    """Parse slice rules from a CLI spec string."""
    return parse_slice_rules(spec)


def apply_slicing(raw: str, rules: list[SliceRule]) -> str:
    """Apply slice rules to a raw log line, returning the (possibly modified) line."""
    if not rules:
        return raw
    return slice_line(raw, rules)
