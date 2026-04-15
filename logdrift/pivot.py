"""Cross-field pivot table: count co-occurrences of two JSON field values."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Optional, Tuple

from logdrift.parser import parse_line, get_json_path_value


Class = Dict[str, Dict[str, int]]


class PivotTable:
    """Track co-occurrence counts for *row_field* × *col_field*."""

    def __init__(self, row_field: str, col_field: str) -> None:
        if not row_field or not col_field:
            raise ValueError("row_field and col_field must be non-empty strings.")
        self._row_field = row_field
        self._col_field = col_field
        self._table: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @property
    def row_field(self) -> str:
        return self._row_field

    @property
    def col_field(self) -> str:
        return self._col_field

    def add(self, line: str) -> Optional[Tuple[str, str]]:
        """Record *line*; return (row_key, col_key) or None if either field absent."""
        parsed = parse_line(line)
        if parsed is None:
            return None
        row_val = get_json_path_value(parsed, self._row_field)
        col_val = get_json_path_value(parsed, self._col_field)
        if row_val is None or col_val is None:
            return None
        rk, ck = str(row_val), str(col_val)
        self._table[rk][ck] += 1
        return rk, ck

    def get(self, row_key: str, col_key: str) -> int:
        return self._table.get(row_key, {}).get(col_key, 0)

    def row_keys(self):
        return sorted(self._table.keys())

    def col_keys(self):
        cols: set = set()
        for sub in self._table.values():
            cols.update(sub.keys())
        return sorted(cols)

    def reset(self) -> None:
        self._table.clear()

    def format_table(self) -> str:
        rows = self.row_keys()
        cols = self.col_keys()
        if not rows:
            return f"pivot[{self._row_field} x {self._col_field}]: no data"
        col_w = max((len(c) for c in cols), default=4)
        row_w = max((len(r) for r in rows), default=4)
        header = f"{'':>{row_w}}  " + "  ".join(f"{c:>{col_w}}" for c in cols)
        lines = [f"pivot: {self._row_field} x {self._col_field}", header]
        for r in rows:
            cells = "  ".join(f"{self.get(r, c):>{col_w}}" for c in cols)
            lines.append(f"{r:>{row_w}}  {cells}")
        return "\n".join(lines)
