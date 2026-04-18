"""Merge fields from multiple JSON log lines into a single output line."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from logdrift.parser import parse_line


def parse_merge_fields(spec: Optional[str]) -> list[str]:
    """Parse a comma-separated list of field names to merge on."""
    if not spec:
        return []
    return [f.strip() for f in spec.split(",") if f.strip()]


@dataclass
class LineMerger:
    key_field: str
    merge_fields: list[str]
    max_keys: int = 1000
    _store: dict[str, dict] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.key_field.strip():
            raise ValueError("key_field must not be empty")
        if not self.merge_fields:
            raise ValueError("merge_fields must not be empty")
        if self.max_keys < 1:
            raise ValueError("max_keys must be >= 1")

    def add(self, line: str) -> Optional[str]:
        """Accumulate merge fields; return key if new, None otherwise."""
        data = parse_line(line)
        if data is None:
            return None
        key = data.get(self.key_field)
        if key is None:
            return None
        key = str(key)
        if key not in self._store:
            if len(self._store) >= self.max_keys:
                oldest = next(iter(self._store))
                del self._store[oldest]
            self._store[key] = {}
        for f in self.merge_fields:
            if f in data:
                self._store[key][f] = data[f]
        return key

    def get_merged(self, key: str) -> Optional[dict]:
        return self._store.get(key)

    def keys(self) -> list[str]:
        return list(self._store.keys())

    def format_summary(self) -> str:
        lines = ["=== Merge Summary ==="]
        for key, fields in self._store.items():
            lines.append(f"  {key}: {fields}")
        return "\n".join(lines)
