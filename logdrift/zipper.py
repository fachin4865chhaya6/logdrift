"""Field zipping: combine multiple JSON fields into a single list or dict field."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class ZipRule:
    sources: list[str]
    dest: str
    as_dict: bool = False

    def __post_init__(self):
        if not self.sources:
            raise ValueError("sources must not be empty")
        if not self.dest or not self.dest.strip():
            raise ValueError("dest must not be empty")

    def apply(self, data: dict) -> dict:
        values = [data.get(s) for s in self.sources]
        if self.as_dict:
            data[self.dest] = {s: v for s, v in zip(self.sources, values)}
        else:
            data[self.dest] = values
        return data


def parse_zip_rules(spec: Optional[str]) -> list[ZipRule]:
    """Parse zip rules from a string like 'a,b->dest' or 'a,b->dest:dict'."""
    if not spec or not spec.strip():
        return []
    rules = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        as_dict = False
        if part.endswith(":dict"):
            as_dict = True
            part = part[:-5]
        if "->" not in part:
            raise ValueError(f"Invalid zip rule (missing '->'): {part!r}")
        sources_str, dest = part.split("->", 1)
        sources = [s.strip() for s in sources_str.split(",") if s.strip()]
        rules.append(ZipRule(sources=sources, dest=dest.strip(), as_dict=as_dict))
    return rules


def zip_json_fields(line: str, rules: list[ZipRule]) -> str:
    if not rules:
        return line
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return line
    if not isinstance(data, dict):
        return line
    for rule in rules:
        data = rule.apply(data)
    return json.dumps(data)


def zip_line(raw: str, rules: list[ZipRule]) -> str:
    return zip_json_fields(raw, rules)
