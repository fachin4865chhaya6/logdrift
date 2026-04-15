"""Line correlation: group log lines by a shared field value within a time window."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logdrift.parser import parse_line, get_json_path_value


@dataclass
class Correlator:
    """Groups matched log lines by a correlation key within a sliding window."""

    corr_field: str
    window_seconds: float = 60.0
    _buckets: Dict[str, List[dict]] = field(default_factory=lambda: defaultdict(list))
    _timestamps: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        if not self.corr_field:
            raise ValueError("corr_field must be a non-empty string")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_seconds
        expired = [
            key for key, times in self._timestamps.items()
            if times and times[-1] < cutoff
        ]
        for key in expired:
            del self._buckets[key]
            del self._timestamps[key]

    def add(self, raw_line: str, now: Optional[float] = None) -> Optional[str]:
        """Add a raw log line. Returns the correlation key if the line was bucketed."""
        now = now if now is not None else time.monotonic()
        self._evict(now)
        parsed = parse_line(raw_line)
        if parsed is None:
            return None
        value = get_json_path_value(parsed, self.corr_field)
        if value is None:
            return None
        key = str(value)
        self._buckets[key].append(parsed)
        self._timestamps[key].append(now)
        return key

    def get_group(self, key: str) -> List[dict]:
        """Return all buffered lines for a given correlation key."""
        return list(self._buckets.get(key, []))

    def group_size(self, key: str) -> int:
        return len(self._buckets.get(key, []))

    def keys(self) -> List[str]:
        return list(self._buckets.keys())

    def reset(self) -> None:
        self._buckets.clear()
        self._timestamps.clear()


def parse_corr_field(value: Optional[str]) -> Optional[str]:
    """Parse and validate a correlation field name from CLI input."""
    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped
