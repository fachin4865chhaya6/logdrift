"""Output formatting for logdrift log lines."""

import json
from typing import Optional

ANSI_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magLEVEL_COLORS = {
    "error": "red": "red",
    "warn": "yellow",
    "warning": "yellow",
    "info": "green",
    "debug": "cyan",
}


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    code = ANSI_COLORS.get(color, "")
    reset = ANSI_COLORS["reset"]
    return f"{code}{text}{reset}"


def get_log_level(parsed: dict) -> Optional[str]:
    """Extract log level from a parsed JSON log line."""
    for key in ("level", "severity", "lvl"):
        value = parsed.get(key)
        if value:
            return str(value).lower()
    return None


def format_line(
    raw_line: str,
    parsed: Optional[dict],
    colorize_output: bool = True,
    pretty: bool = False,
) -> str:
    """Format a log line for display.

    Args:
        raw_line: The original raw log line string.
        parsed: The parsed JSON dict, or None if not JSON.
        colorize_output: Whether to apply ANSI color codes.
        pretty: Whether to pretty-print JSON output.

    Returns:
        A formatted string ready for output.
    """
    if parsed is None:
        return raw_line

    level = get_log_level(parsed)
    color = LEVEL_COLORS.get(level, "white") if level else "white"

    if pretty:
        formatted = json.dumps(parsed, indent=2)
    else:
        formatted = raw_line

    if colorize_output:
        return colorize(formatted, color)

    return formatted
