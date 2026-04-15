"""Output handling for logdrift.

Responsible for writing filtered and formatted log lines
to the appropriate stream, updating stats, and printing summaries.
"""

import sys
from typing import Optional, TextIO

from logdrift.formatter import format_line
from logdrift.highlighter import highlight_keywords
from logdrift.stats import LogStats, record_line, format_summary
from logdrift.sampler import Sampler


def _get_output_stream(output_file: Optional[str]) -> TextIO:
    """Return a writable stream: a file if path given, else stdout."""
    if output_file:
        return open(output_file, "a", encoding="utf-8")
    return sys.stdout


def write_line(
    raw: str,
    matched: bool,
    stats: LogStats,
    stream: TextIO,
    keywords: Optional[list] = None,
    color: bool = True,
    sampler: Optional[Sampler] = None,
) -> None:
    """Write a single log line to the stream if matched and sampled.

    Args:
        raw: The raw log line string.
        matched: Whether the line passed all filters.
        stats: LogStats instance to update.
        stream: Output stream to write to.
        keywords: Optional list of keywords to highlight.
        color: Whether to apply color formatting.
        sampler: Optional Sampler to sub-sample matched lines.
    """
    if not matched:
        record_line(stats, raw, matched=False)
        return

    if sampler is not None and not sampler.should_keep():
        record_line(stats, raw, matched=False)
        return

    record_line(stats, raw, matched=True)
    formatted = format_line(raw, color=color)
    if keywords:
        formatted = highlight_keywords(formatted, keywords, color=color)
    stream.write(formatted + "\n")
    stream.flush()


def write_summary(stats: LogStats, stream: TextIO) -> None:
    """Write a formatted stats summary to the given stream."""
    summary = format_summary(stats)
    stream.write(summary + "\n")
    stream.flush()


def run_output(
    lines,
    stats: LogStats,
    output_file: Optional[str] = None,
    keywords: Optional[list] = None,
    color: bool = True,
    sampler: Optional[Sampler] = None,
    show_summary: bool = False,
) -> None:
    """Process an iterable of (raw_line, matched) tuples and write output.

    Args:
        lines: Iterable of (raw_line: str, matched: bool) tuples.
        stats: LogStats instance to track counts.
        output_file: Optional path to write output to instead of stdout.
        keywords: Optional list of highlight keywords.
        color: Whether to apply color formatting.
        sampler: Optional Sampler for sub-sampling matched lines.
        show_summary: If True, print stats summary after processing.
    """
    stream = _get_output_stream(output_file)
    try:
        for raw, matched in lines:
            write_line(
                raw,
                matched=matched,
                stats=stats,
                stream=stream,
                keywords=keywords,
                color=color,
                sampler=sampler,
            )
        if show_summary:
            write_summary(stats, stream=sys.stderr)
    finally:
        if output_file and not stream.closed:
            stream.close()
