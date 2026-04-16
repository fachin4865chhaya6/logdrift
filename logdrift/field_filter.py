"""Field-based filtering: include or exclude lines by JSON field values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from logdrift.parser import parse_line, get_json_path_value


@dataclass
class FieldFilter:
    include: dict[str, str] = field(default_factory=dict)
    exclude: dict[str, str] = field(default_factory=dict)

    def passes(self, line: str) -> bool:
        parsed = parse_line(line)
        if parsed is None:
            return True
        for path, value in self.include.items():
            actual = get_json_path_value(parsed, path)
            if str(actual) != value:
                return False
        for path, value in self.exclude.items():
            actual = get_json_path_value(parsed, path)
            if str(actual) == value:
                return False
        return True


def parse_field_filter_args(include_raw: Optional[str], exclude_raw: Optional[str]) -> FieldFilter:
    """Parse comma-separated key=value pairs for include/exclude filters."""
    return FieldFilter(
        include=_parse_kv(include_raw),
        exclude=_parse_kv(exclude_raw),
    )


def _parse_kv(raw: Optional[str]) -> dict[str, str]:
    if not raw:
        return {}
    result: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if "=" not in part:
            raise ValueError(f"Invalid field filter expression: {part!r}")
        key, _, value = part.partition("=")
        result[key.strip()] = value.strip()
    return result
