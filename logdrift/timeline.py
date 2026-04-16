"""Groups log lines into time buckets for timeline analysis."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math

from logdrift.parser import parse_line, get_json_path_value


@dataclass
class Timeline:
    bucket_seconds: int
    time_field: str

    _buckets: Dict[int, int] = field(default_factory=lambda: defaultdict(int), init=False)

    def __post_init__(self) -> None:
        if self.bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be positive")
        if not self.time_field:
            raise ValueError("time_field must not be empty")

    @property
    def buckets(self) -> Dict[int, int]:
        return dict(self._buckets)

    def add(self, line: str) -> Optional[int]:
        """Parse line, extract timestamp, increment bucket. Returns bucket key or None."""
        data = parse_line(line)
        if data is None:
            return None
        raw = get_json_path_value(data, self.time_field)
        if raw is None:
            return None
        try:
            ts = float(raw)
        except (TypeError, ValueError):
            return None
        bucket = int(math.floor(ts / self.bucket_seconds)) * self.bucket_seconds
        self._buckets[bucket] += 1
        return bucket

    def format_summary(self) -> List[str]:
        if not self._buckets:
            return ["timeline: no data"]
        lines = ["timeline summary:"]
        for bucket in sorted(self._buckets):
            count = self._buckets[bucket]
            bar = "#" * min(count, 40)
            lines.append(f"  t={bucket:>12}  {count:>5}  {bar}")
        return lines


def parse_timeline_args(time_field: Optional[str], bucket_seconds: Optional[int]) -> Optional[Timeline]:
    if not time_field:
        return None
    return Timeline(bucket_seconds=bucket_seconds or 60, time_field=time_field)
