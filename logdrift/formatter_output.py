from __future__ import annotations

from typing import Optional

from logdrift.formatter import format_line
from logdrift.highlighter import highlight_keywords, parse_highlight_keywords


def make_highlight_keywords(raw: Optional[str]) -> list[str]:
    """Parse highlight keyword spec from CLI arg."""
    return parse_highlight_keywords(raw)


def apply_formatting(
    raw: str,
    parsed: Optional[dict],
    *,
    highlight: list[str],
    no_color: bool = False,
    fields: Optional[list[str]] = None,
) -> str:
    """Format and optionally highlight a log line.

    Args:
        raw: The original raw log line.
        parsed: Parsed JSON dict, or None for plain text.
        highlight: List of keywords to highlight.
        no_color: If True, skip colorization.
        fields: Optional list of JSON fields to include in output.

    Returns:
        The formatted string ready for output.
    """
    formatted = format_line(raw, parsed, no_color=no_color, fields=fields)
    if highlight and not no_color:
        formatted = highlight_keywords(formatted, highlight)
    return formatted
