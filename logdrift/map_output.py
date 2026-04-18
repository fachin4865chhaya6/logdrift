"""Output helpers for the field mapper."""
from __future__ import annotations

from logdrift.mapper import FieldMapper, parse_mapper_spec, map_line


def make_mappers(spec: str | None) -> list[FieldMapper]:
    """Return a list of FieldMapper instances from a CLI spec string."""
    return parse_mapper_spec(spec)


def apply_mapping(line: str, mappers: list[FieldMapper]) -> str:
    """Apply all mappers to *line* and return the (possibly modified) result."""
    return map_line(line, mappers)
