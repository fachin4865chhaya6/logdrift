"""Field-based log aggregation: count occurrences grouped by a JSON field value."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from logdrift.parser import parse_line, get_json_path_value


class Aggregator:
    """Accumulates log lines and counts them grouped by a field's value."""

    def __init__(self, field: str) -> None:
        if not field:
            raise ValueError("Aggregator field must be a non-empty string.")
        self._field = field
        self._counts: Dict[str, int] = defaultdict(int)
        self._total = 0

    @property
    def field(self) -> str:
        return self._field

    @property
    def total(self) -> int:
        return self._total

    def add(self, line: str) -> Optional[str]:
        """Record *line* and return the bucket key (or None if field absent)."""
        self._total += 1
        parsed = parse_line(line)
        if parsed is None:
            return None
        value = get_json_path_value(parsed, self._field)
        if value is None:
            return None
        key = str(value)
        self._counts[key] += 1
        return key

    def counts(self) -> Dict[str, int]:
        """Return a plain dict copy of current bucket counts."""
        return dict(self._counts)

    def top(self, n: int = 10) -> List[Tuple[str, int]]:
        """Return the top *n* buckets sorted by count descending."""
        return sorted(self._counts.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def reset(self) -> None:
        """Clear all accumulated state."""
        self._counts.clear()
        self._total = 0

    def format_summary(self, top_n: int = 10) -> str:
        """Return a human-readable summary table."""
        rows = self.top(top_n)
        if not rows:
            return f"aggregator[{self._field}]: no data"
        lines = [f"aggregator field={self._field!r} total={self._total}"]
        width = max(len(k) for k, _ in rows)
        for key, count in rows:
            pct = 100.0 * count / self._total if self._total else 0.0
            lines.append(f"  {key:<{width}}  {count:>6}  ({pct:.1f}%)")
        return "\n".join(lines)


def parse_aggregate_field(value: Optional[str]) -> Optional[str]:
    """Return stripped field name or None when *value* is empty/None."""
    if not value:
        return None
    stripped = value.strip()
    return stripped if stripped else None
