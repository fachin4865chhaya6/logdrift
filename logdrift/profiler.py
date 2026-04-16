"""Field value profiler: tracks distinct values and frequencies for a JSON field."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional
from logdrift.parser import parse_line, get_json_path_value


@dataclass
class FieldProfiler:
    _field: str
    _limit: int = 10
    _counts: Counter = field(default_factory=Counter)
    _total: int = 0

    def __post_init__(self) -> None:
        if not self._field:
            raise ValueError("field must not be empty")
        if self._limit < 1:
            raise ValueError("limit must be at least 1")

    @property
    def field(self) -> str:
        return self._field

    @property
    def total(self) -> int:
        return self._total

    def add(self, line: str) -> Optional[str]:
        data = parse_line(line)
        if data is None:
            return None
        value = get_json_path_value(data, self._field)
        if value is None:
            return None
        key = str(value)
        self._counts[key] += 1
        self._total += 1
        return key

    def top(self) -> list[tuple[str, int]]:
        return self._counts.most_common(self._limit)

    def format_summary(self) -> str:
        lines = [f"Profile [{self._field}] — {self._total} values recorded:"]
        for value, count in self.top():
            pct = (count / self._total * 100) if self._total else 0
            lines.append(f"  {value}: {count} ({pct:.1f}%)")
        return "\n".join(lines)


def parse_profile_field(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    return value.strip()


def make_profiler(field_str: Optional[str], limit: int = 10) -> Optional[FieldProfiler]:
    f = parse_profile_field(field_str)
    if f is None:
        return None
    return FieldProfiler(_field=f, _limit=limit)
