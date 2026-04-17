"""Helpers for wiring field truncation into the output pipeline."""
from __future__ import annotations

from typing import Optional

from logdrift.truncator import parse_truncate_fields, truncate_line


def make_truncate_fields(spec: Optional[str]) -> dict[str, int]:
    """Return a truncation map from *spec*, or an empty dict if spec is None/empty."""
    if not spec:
        return {}
    return parse_truncate_fields(spec)


def apply_truncation(raw: str, fields: dict[str, int]) -> str:
    """Apply truncation to *raw* using *fields*; returns raw unchanged if fields empty."""
    if not fields:
        return raw
    return truncate_line(raw, fields)
