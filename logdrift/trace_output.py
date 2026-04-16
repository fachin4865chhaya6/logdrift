"""Output helpers for the trace collector."""
from __future__ import annotations
from typing import Callable, List, Optional
from logdrift.tracer import TraceCollector, parse_trace_field


def make_trace_collector(
    trace_field: Optional[str],
    max_traces: int = 1000,
) -> Optional[TraceCollector]:
    if not trace_field:
        return None
    return TraceCollector(
        trace_field=parse_trace_field(trace_field),
        max_traces=max_traces,
    )


def record_for_tracing(
    collector: Optional[TraceCollector],
    line: str,
) -> Optional[str]:
    if collector is None:
        return None
    return collector.add(line)


def _default_trace_callback(trace_id: str, lines: List[str]) -> None:
    print(f"[trace:{trace_id}] {len(lines)} line(s)")
    for ln in lines:
        print(f"  {ln}")


def write_trace_summary(
    collector: Optional[TraceCollector],
    callback: Optional[Callable[[str, List[str]], None]] = None,
) -> None:
    if collector is None:
        return
    cb = callback or _default_trace_callback
    for tid in collector.all_trace_ids():
        cb(tid, collector.get_trace(tid))
