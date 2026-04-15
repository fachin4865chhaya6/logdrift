"""Output writer module for logdrift.

Handles writing filtered and formatted log lines to stdout or a file,
with optional stats summary at the end.
"""

import sys
from typing import Optional, TextIO

from logdrift.formatter import format_line
from logdrift.highlighter import highlight_keywords
from logdrift.stats import LogStats, record_line, format_summary


def _get_output_stream(output_path: Optional[str]) -> TextIO:
    """Return a writable stream: stdout if no path given, else open file."""
    if output_path is None:
        return sys.stdout
    return open(output_path, "w", encoding="utf-8")


def write_line(
    raw: str,
    matched: bool,
    stats: LogStats,
    stream: TextIO,
    *,
    color: bool = True,
    keywords: Optional[list] = None,
) -> None:
    """Format and write a single log line to the output stream.

    Args:
        raw: The raw log line string.
        matched: Whether the line passed all filters.
        stats: LogStats instance to update.
        stream: Output stream to write to.
        color: Whether to apply ANSI color formatting.
        keywords: Optional list of keywords to highlight.
    """
    record_line(stats, raw, matched=matched)

    if not matched:
        return

    formatted = format_line(raw, color=color)

    if keywords:
        formatted = highlight_keywords(formatted, keywords)

    stream.write(formatted + "\n")
    stream.flush()


def write_summary(stats: LogStats, stream: TextIO, *, color: bool = True) -> None:
    """Write a stats summary block to the output stream.

    Args:
        stats: Populated LogStats instance.
        stream: Output stream to write to.
        color: Whether to apply ANSI color formatting.
    """
    summary = format_summary(stats, color=color)
    stream.write(summary + "\n")
    stream.flush()


def run_output(
    lines: list,
    output_path: Optional[str] = None,
    *,
    color: bool = True,
    keywords: Optional[list] = None,
    show_summary: bool = False,
) -> LogStats:
    """Process a list of (raw, matched) tuples and write output.

    Returns the populated LogStats instance.
    """
    stats = LogStats()
    stream = _get_output_stream(output_path)
    try:
        for raw, matched in lines:
            write_line(raw, matched, stats, stream, color=color, keywords=keywords)
        if show_summary:
            write_summary(stats, stream, color=color)
    finally:
        if output_path is not None:
            stream.close()
    return stats
