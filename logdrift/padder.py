from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class PadRule:
    field: str
    width: int
    align: str = "left"  # "left", "right", "center"
    fill_char: str = " "

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("field must not be empty")
        if self.width <= 0:
            raise ValueError("width must be a positive integer")
        if self.align not in ("left", "right", "center"):
            raise ValueError("align must be 'left', 'right', or 'center'")
        if len(self.fill_char) != 1:
            raise ValueError("fill_char must be exactly one character")

    def apply(self, value: Any) -> str:
        text = str(value)
        if self.align == "left":
            return text.ljust(self.width, self.fill_char)
        elif self.align == "right":
            return text.rjust(self.width, self.fill_char)
        else:
            return text.center(self.width, self.fill_char)


def parse_pad_rules(spec: str | None) -> list[PadRule]:
    """Parse a comma-separated list of pad rule specs.

    Each spec has the form:  field:width[:align[:fill_char]]
    Example: "status:10:right:0,name:20:left"
    """
    if not spec or not spec.strip():
        return []
    rules: list[PadRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split(":")
        if len(tokens) < 2:
            raise ValueError(f"invalid pad rule spec: {part!r}")
        field = tokens[0].strip()
        try:
            width = int(tokens[1].strip())
        except ValueError:
            raise ValueError(f"invalid width in pad rule: {part!r}")
        align = tokens[2].strip() if len(tokens) > 2 else "left"
        fill_char = tokens[3] if len(tokens) > 3 else " "
        rules.append(PadRule(field=field, width=width, align=align, fill_char=fill_char))
    return rules


def pad_json_fields(data: dict, rules: list[PadRule]) -> dict:
    result = dict(data)
    for rule in rules:
        if rule.field in result:
            result[rule.field] = rule.apply(result[rule.field])
    return result


def pad_line(raw: str, rules: list[PadRule]) -> str:
    if not rules:
        return raw
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
    if not isinstance(data, dict):
        return raw
    return json.dumps(pad_json_fields(data, rules))
