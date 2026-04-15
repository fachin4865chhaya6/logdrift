"""Output helpers for logdrift.

Handles writing filtered/formatted lines to a stream, optional summary
printing, and now optional per-second rate limiting via :class:`Throttle`.
"""

from __future__ import annotations

import sys
from typing import IO, Iterable, Optional

from logdrift.formatter import format_line
from logdrift.highlighter import highlight_keywords
from logdrift.stats import LogStats, record_line, format_summary
from logdrift.throttle import Throttle


def _get_output_stream(path: Optional[str]) -> IO[str]:
    """Return an open file handle for *path*, or *stdout* when path is None."""
    if path:
        return open(path, "a", encoding="utf-8")  # noqa: WPS515
    return sys.stdout


def write_line(
    line: str,
    matched: bool,
    stream: IO[str],
    stats: LogStats,
    keywords: Optional[list] = None,
    colorize: bool = True,
    throttle: Optional[Throttle] = None,
) -> None:
    """Record *line* in *stats* and, if *matched*, write it to *stream*.

    When a :class:`~logdrift.throttle.Throttle` is supplied and the current
    rate exceeds the configured limit the line is silently dropped (counted
    as skipped in stats).
    """
    record_line(stats, line, matched)
    if not matched:
        return

    if throttle is not None and not throttle.allow():
        # Throttled lines are not written; already counted via record_line.
        return

    formatted = format_line(line, colorize=colorize)
    if keywords:
        formatted = highlight_keywords(formatted, keywords)
    stream.write(formatted + "\n")
    stream.flush()


def write_summary(stats: LogStats, stream: IO[str]) -> None:
    """Write a formatted summary of *stats* to *stream*."""
    stream.write(format_summary(stats) + "\n")
    stream.flush()


def run_output(
    lines: Iterable[tuple[str, bool]],
    stream: IO[str],
    stats: LogStats,
    keywords: Optional[list] = None,
    colorize: bool = True,
    show_summary: bool = False,
    throttle: Optional[Throttle] = None,
) -> None:
    """Consume *(line, matched)* pairs from *lines* and write matched ones.

    Parameters
    ----------
    lines:
        Iterable of ``(raw_line, was_matched)`` tuples.
    stream:
        Output destination.
    stats:
        Mutable stats object updated for every line.
    keywords:
        Optional highlight keyword list.
    colorize:
        Whether to apply ANSI colour codes.
    show_summary:
        If *True*, print a stats summary after all lines are consumed.
    throttle:
        Optional rate limiter; dropped lines are not written to *stream*.
    """
    for line, matched in lines:
        write_line(
            line,
            matched,
            stream,
            stats,
            keywords=keywords,
            colorize=colorize,
            throttle=throttle,
        )
    if show_summary:
        write_summary(stats, stream)
