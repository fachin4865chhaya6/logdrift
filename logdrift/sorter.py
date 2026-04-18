from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from logdrift.parser import parse_line, get_json_path_value


def parse_sort_field(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    return value.strip()


def parse_sort_limit(value: Optional[str]) -> int:
    if value is None:
        return 0
    n = int(value)
    if n < 0:
        raise ValueError(f"sort limit must be non-negative, got {n}")
    return n


@dataclass
class LineSorter:
    sort_field: str
    limit: int = 0
    reverse: bool = False
    _lines: List[tuple] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        if not self.sort_field:
            raise ValueError("sort_field must not be empty")
        if self.limit < 0:
            raise ValueError("limit must be non-negative")

    @property
    def total(self) -> int:
        return len(self._lines)

    def add(self, raw: str) -> None:
        parsed = parse_line(raw)
        if parsed is None:
            return
        val = get_json_path_value(parsed, self.sort_field)
        if val is None:
            return
        self._lines.append((val, raw))

    def sorted_lines(self) -> List[str]:
        ordered = sorted(self._lines, key=lambda t: t[0], reverse=self.reverse)
        if self.limit:
            ordered = ordered[: self.limit]
        return [raw for _, raw in ordered]

    def format_summary(self) -> str:
        lines = self.sorted_lines()
        if not lines:
            return "(no sortable lines)"
        return "\n".join(lines)
