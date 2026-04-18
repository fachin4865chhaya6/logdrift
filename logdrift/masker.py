"""Field value masking — partially obscure JSON field values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from logdrift.parser import parse_line


@dataclass
class MaskRule:
    field_name: str
    keep_chars: int = 4
    mask_char: str = "*"

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name must not be empty")
        if self.keep_chars < 0:
            raise ValueError("keep_chars must be >= 0")
        if len(self.mask_char) != 1:
            raise ValueError("mask_char must be a single character")

    def apply(self, value: str) -> str:
        if len(value) <= self.keep_chars:
            return self.mask_char * len(value)
        visible = value[-self.keep_chars:] if self.keep_chars else ""
        return self.mask_char * (len(value) - self.keep_chars) + visible


def parse_mask_rules(spec: str | None) -> list[MaskRule]:
    """Parse 'field:keep' or 'field' entries separated by commas."""
    if not spec:
        return []
    rules: list[MaskRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            fname, keep_str = part.split(":", 1)
            rules.append(MaskRule(field_name=fname.strip(), keep_chars=int(keep_str.strip())))
        else:
            rules.append(MaskRule(field_name=part))
    return rules


def mask_json_fields(data: dict[str, Any], rules: list[MaskRule]) -> dict[str, Any]:
    result = dict(data)
    for rule in rules:
        if rule.field_name in result:
            original = str(result[rule.field_name])
            result[rule.field_name] = rule.apply(original)
    return result


def mask_line(line: str, rules: list[MaskRule]) -> str:
    if not rules:
        return line
    data = parse_line(line)
    if data is None:
        return line
    import json
    return json.dumps(mask_json_fields(data, rules))
