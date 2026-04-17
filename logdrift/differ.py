"""Field-level diff tracking between consecutive matching log lines."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from logdrift.parser import parse_line, get_json_path_value


@dataclass
class LineDiffer:
    fields: list[str]
    _prev: dict[str, Any] = field(default_factory=dict, init=False)
    _total: int = field(default=0, init=False)
    _changes: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.fields:
            raise ValueError("fields must not be empty")

    @property
    def total(self) -> int:
        return self._total

    @property
    def changes(self) -> int:
        return self._changes

    def diff(self, line: str) -> dict[str, tuple[Any, Any]] | None:
        """Return changed fields as {field: (old, new)} or None for plain text."""
        parsed = parse_line(line)
        if parsed is None:
            return None
        self._total += 1
        result: dict[str, tuple[Any, Any]] = {}
        for f in self.fields:
            new_val = get_json_path_value(parsed, f)
            old_val = self._prev.get(f)
            if old_val != new_val:
                result[f] = (old_val, new_val)
                self._prev[f] = new_val
        if result:
            self._changes += 1
        return result

    def format_diff(self, diffs: dict[str, tuple[Any, Any]]) -> str:
        parts = [f"{f}: {old!r} -> {new!r}" for f, (old, new) in diffs.items()]
        return "[diff] " + ", ".join(parts) if parts else ""

    def reset(self) -> None:
        self._prev.clear()
        self._total = 0
        self._changes = 0


def parse_diff_fields(value: str | None) -> list[str]:
    if not value:
        return []
    return [f.strip() for f in value.split(",") if f.strip()]
