"""Wire alert rules into the logdrift output pipeline."""

from __future__ import annotations

import sys
from typing import Callable, List, Optional, TextIO

from logdrift.alerter import AlertRule, check_alerts, parse_alert_rules
from logdrift.formatter import colorize


def make_alert_rules(
    specs: Optional[str],
    threshold: int = 1,
    window: float = 60.0,
) -> List[AlertRule]:
    """Build alert rules from CLI-style spec string."""
    return parse_alert_rules(specs, threshold=threshold, window=window)


def _default_alert_callback(
    rule: AlertRule,
    line: str,
    stream: TextIO = sys.stderr,
) -> None:
    """Print a formatted alert banner to *stream*."""
    banner = colorize(
        f"[ALERT] rule={rule.name!r} threshold={rule.threshold} "
        f"window={rule.window}s matched: {line.rstrip()}",
        color="red",
    )
    stream.write(banner + "\n")
    stream.flush()


def make_alert_callback(
    stream: TextIO = sys.stderr,
) -> Callable[[AlertRule, str], None]:
    """Return a callback that writes alert banners to *stream*."""
    def _cb(rule: AlertRule, line: str) -> None:
        _default_alert_callback(rule, line, stream=stream)
    return _cb


def process_alerts(
    line: str,
    rules: List[AlertRule],
    callback: Optional[Callable[[AlertRule, str], None]] = None,
    stream: TextIO = sys.stderr,
) -> None:
    """Check *line* against *rules* and fire alerts as needed.

    If *callback* is None a default stderr banner writer is used.
    """
    if not rules:
        return
    cb = callback if callback is not None else make_alert_callback(stream=stream)
    check_alerts(line, rules, cb)
