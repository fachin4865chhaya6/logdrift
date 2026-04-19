"""Output helpers for field zipping."""
from __future__ import annotations
from typing import Optional
from logdrift.zipper import ZipRule, parse_zip_rules, zip_line


def make_zip_rules(spec: Optional[str]) -> list[ZipRule]:
    return parse_zip_rules(spec)


def apply_zipping(raw: str, rules: list[ZipRule]) -> str:
    if not rules:
        return raw
    return zip_line(raw, rules)
