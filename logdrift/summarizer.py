from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LineSummarizer:
    max_samples: int = 5
    _counts: Dict[str, int] = field(default_factory=dict, init=False)
    _samples: Dict[str, List[str]] = field(default_factory=dict, init=False)
    _total: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_samples < 1:
            raise ValueError("max_samples must be at least 1")

    @property
    def total(self) -> int:
        return self._total

    @property
    def buckets(self) -> Dict[str, int]:
        return dict(self._counts)

    def add(self, bucket: str, line: str) -> None:
        if not bucket:
            raise ValueError("bucket must not be empty")
        self._total += 1
        self._counts[bucket] = self._counts.get(bucket, 0) + 1
        samples = self._samples.setdefault(bucket, [])
        if len(samples) < self.max_samples:
            samples.append(line)

    def get_samples(self, bucket: str) -> List[str]:
        return list(self._samples.get(bucket, []))

    def format_summary(self) -> str:
        if not self._counts:
            return "No data summarized."
        lines = [f"Summary ({self._total} total lines):"]
        for bucket, count in sorted(self._counts.items(), key=lambda x: -x[1]):
            lines.append(f"  [{bucket}] {count} occurrence(s)")
            for sample in self._samples.get(bucket, []):
                truncated = sample if len(sample) <= 80 else sample[:77] + "..."
                lines.append(f"    - {truncated}")
        return "\n".join(lines)


def parse_summarize_field(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    return value.strip()


def make_summarizer(field_arg: Optional[str], max_samples: int = 5) -> Optional[LineSummarizer]:
    if not parse_summarize_field(field_arg):
        return None
    return LineSummarizer(max_samples=max_samples)
