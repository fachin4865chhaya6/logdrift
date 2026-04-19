"""Output helpers for field pinning."""
from __future__ import annotations

from typing import Optional

from logdrift.pinner import FieldPinner, parse_pin_fields, pin_line


def make_field_pinner(spec: Optional[str]) -> Optional[FieldPinner]:
    """Build a FieldPinner from a CLI spec string, or return None if not configured."""
    fields = parse_pin_fields(spec)
    if not fields:
        return None
    return FieldPinner(pin_fields=fields)


def apply_pinning(raw: str, pinner: Optional[FieldPinner]) -> str:
    """Apply field pinning and return the (possibly reordered) line."""
    return pin_line(raw, pinner)
