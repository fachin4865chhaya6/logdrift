"""Wire Aggregator and PivotTable into the output pipeline."""

from __future__ import annotations

from typing import IO, Optional

from logdrift.aggregator import Aggregator, parse_aggregate_field
from logdrift.pivot import PivotTable


def make_aggregator(field: Optional[str]) -> Optional[Aggregator]:
    """Return an :class:`Aggregator` when *field* is non-empty, else None."""
    parsed = parse_aggregate_field(field)
    if parsed is None:
        return None
    return Aggregator(parsed)


def make_pivot(row_field: Optional[str], col_field: Optional[str]) -> Optional[PivotTable]:
    """Return a :class:`PivotTable` when both fields are non-empty, else None."""
    from logdrift.aggregator import parse_aggregate_field as _p
    r = _p(row_field)
    c = _p(col_field)
    if r is None or c is None:
        return None
    return PivotTable(r, c)


def record_for_aggregation(
    line: str,
    aggregator: Optional[Aggregator],
    pivot: Optional[PivotTable],
) -> None:
    """Feed *line* into active aggregation objects (no-op when None)."""
    if aggregator is not None:
        aggregator.add(line)
    if pivot is not None:
        pivot.add(line)


def write_aggregation_summary(
    stream: IO[str],
    aggregator: Optional[Aggregator],
    pivot: Optional[PivotTable],
    top_n: int = 10,
) -> None:
    """Write aggregation summaries to *stream* when active."""
    if aggregator is not None:
        stream.write(aggregator.format_summary(top_n=top_n) + "\n")
    if pivot is not None:
        stream.write(pivot.format_table() + "\n")
