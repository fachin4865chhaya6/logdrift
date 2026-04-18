"""Output helpers for field casting."""
from __future__ import annotations
from typing import List, Optional
from logdrift.caster import CastRule, parse_cast_rules, cast_line


def make_cast_rules(spec: Optional[str]) -> List[CastRule]:
    """Return cast rules from CLI spec, or empty list."""
    if not spec:
        return []
    return parse_cast_rules(spec)


def apply_casting(line: str, rules: List[CastRule]) -> str:
    """Apply cast rules to a log line and return the result."""
    if not rules:
        return line
    return cast_line(line, rules)
