"""Keyword highlighting for log output lines."""

import re
from typing import List, Optional

from logdrift.formatter import colorize

# Mapping of highlight color names to ANSI color keys
HIGHLIGHT_COLORS = [
    "yellow",
    "cyan",
    "magenta",
    "blue",
    "green",
]


def highlight_keywords(
    text: str,
    keywords: List[str],
    case_sensitive: bool = False,
) -> str:
    """Wrap each keyword occurrence in the text with a distinct color.

    Args:
        text: The raw log line string to process.
        keywords: List of keyword strings to highlight.
        case_sensitive: Whether matching should be case-sensitive.

    Returns:
        The text with keyword occurrences wrapped in ANSI color codes.
    """
    if not keywords or not text:
        return text

    result = text
    for index, keyword in enumerate(keywords):
        if not keyword:
            continue
        color = HIGHLIGHT_COLORS[index % len(HIGHLIGHT_COLORS)]
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(keyword), flags)

        def _replace(match: re.Match, _color: str = color) -> str:
            return colorize(match.group(0), _color)

        result = pattern.sub(_replace, result)

    return result


def parse_highlight_keywords(raw: Optional[str]) -> List[str]:
    """Parse a comma-separated string of keywords into a list.

    Args:
        raw: Comma-separated keyword string, e.g. "error,timeout,failed".

    Returns:
        List of stripped, non-empty keyword strings.
    """
    if not raw:
        return []
    return [kw.strip() for kw in raw.split(",") if kw.strip()]
