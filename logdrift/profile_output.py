"""Output helpers for field profiling."""
from __future__ import annotations
from typing import Optional, IO
import sys
from logdrift.profiler import FieldProfiler, make_profiler


def make_field_profiler(
    field: Optional[str],
    limit: int = 10,
) -> Optional[FieldProfiler]:
    return make_profiler(field, limit=limit)


def record_for_profiling(profiler: Optional[FieldProfiler], line: str) -> None:
    if profiler is None:
        return
    profiler.add(line)


def write_profile_summary(
    profiler: Optional[FieldProfiler],
    stream: IO[str] = sys.stderr,
) -> None:
    if profiler is None or profiler.total == 0:
        return
    stream.write(profiler.format_summary() + "\n")
