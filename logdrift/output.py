"""Output module: coordinates reading, filtering, redacting, and writing log lines."""

import json
import sys
from typing import Any, Dict, List, Optional

from logdrift.formatter import format_line
from logdrift.highlighter import highlight_keywords, parse_highlight_keywords
from logdrift.parser import filter_line, parse_line
from logdrift.redactor import redact_line
from logdrift.sampler import Sampler
from logdrift.stats import LogStats, format_summary, record_line
from logdrift.tailer import tail_file


def _get_output_stream():
    return sys.stdout


def write_line(
    raw: str,
    stream,
    stats: LogStats,
    highlight_kws: list,
    redact_fields: List[str],
    redact_patterns: List[str],
    matched: bool,
    parsed: Optional[Dict[str, Any]],
) -> None:
    if not matched:
        record_line(stats, matched=False, level=None)
        return

    raw, parsed = redact_line(raw, parsed, redact_fields, redact_patterns)
    formatted = format_line(raw, parsed)
    if highlight_kws:
        formatted = highlight_keywords(formatted, highlight_kws)

    level = None
    if parsed and isinstance(parsed, dict):
        level = parsed.get("level") or parsed.get("severity")

    record_line(stats, matched=True, level=level)
    stream.write(formatted + "\n")


def write_summary(stats: LogStats, stream) -> None:
    stream.write(format_summary(stats) + "\n")


def run_output(
    filepath: str,
    follow: bool = False,
    regex: Optional[str] = None,
    json_filter: Optional[Dict[str, str]] = None,
    level: Optional[str] = None,
    highlight: Optional[str] = None,
    sampler: Optional[Sampler] = None,
    show_stats: bool = False,
    redact_fields: Optional[List[str]] = None,
    redact_patterns: Optional[List[str]] = None,
) -> None:
    stream = _get_output_stream()
    stats = LogStats()
    highlight_kws = parse_highlight_keywords(highlight)
    redact_fields = redact_fields or []
    redact_patterns = redact_patterns or []

    for raw in tail_file(filepath, follow=follow):
        if sampler and not sampler.should_keep():
            continue

        parsed = parse_line(raw)
        matched = filter_line(
            raw,
            parsed,
            regex=regex,
            json_filter=json_filter,
            level=level,
        )

        write_line(
            raw=raw,
            stream=stream,
            stats=stats,
            highlight_kws=highlight_kws,
            redact_fields=redact_fields,
            redact_patterns=redact_patterns,
            matched=matched,
            parsed=parsed,
        )

    if show_stats:
        write_summary(stats, stream)
