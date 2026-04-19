from __future__ import annotations

from typing import Optional

from logdrift.field_selector import parse_field_selector, select_line


def make_field_selector(raw: Optional[str]) -> list[str]:
    """Build a field selector list from a CLI argument."""
    return parse_field_selector(raw)


def apply_field_selection(
    raw: str,
    parsed: Optional[dict],
    fields: list[str],
) -> tuple[str, Optional[dict]]:
    """Apply field selection, returning updated (raw, parsed)."""
    return select_line(raw, parsed, fields)
