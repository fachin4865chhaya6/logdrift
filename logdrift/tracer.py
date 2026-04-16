"""Field-based request/trace ID correlator for grouping related log lines."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from logdrift.parser import parse_line, get_json_path_value


def parse_trace_field(value: Optional[str]) -> str:
    if not value or not value.strip():
        raise ValueError("trace field must be a non-empty string")
    return value.strip()


@dataclass
class TraceCollector:
    trace_field: str
    max_traces: int = 1000
    _traces: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trace_field:
            raise ValueError("trace_field must not be empty")
        if self.max_traces < 1:
            raise ValueError("max_traces must be at least 1")

    @property
    def total(self) -> int:
        return len(self._traces)

    def add(self, line: str) -> Optional[str]:
        parsed = parse_line(line)
        if parsed is None:
            return None
        trace_id = get_json_path_value(parsed, self.trace_field)
        if trace_id is None:
            return None
        key = str(trace_id)
        if key not in self._traces:
            if len(self._traces) >= self.max_traces:
                oldest = next(iter(self._traces))
                del self._traces[oldest]
            self._traces[key] = []
        self._traces[key].append(line)
        return key

    def get_trace(self, trace_id: str) -> List[str]:
        return list(self._traces.get(trace_id, []))

    def all_trace_ids(self) -> List[str]:
        return list(self._traces.keys())

    def format_summary(self) -> str:
        lines = [f"Traces ({self.total} unique '{self.trace_field}' values):"]
        for tid, entries in self._traces.items():
            lines.append(f"  {tid}: {len(entries)} line(s)")
        return "\n".join(lines)
