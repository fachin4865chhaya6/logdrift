"""Output helpers for the field capper."""
from __future__ import annotations

from typing import Optional

from logdrift.capper import CapRule, cap_line, parse_cap_rules


def make_cap_rules(spec: Optional[str]) -> list[CapRule]:
    """Return parsed cap rules or an empty list."""
    return parse_cap_rules(spec) if spec else []


def apply_capping(raw: str, rules: list[CapRule]) -> str:
    """Apply cap rules to a raw log line, returning the (possibly modified) line."""
    if not rules:
        return raw
    return cap_line(raw, rules)
