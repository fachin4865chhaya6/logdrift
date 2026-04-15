"""Alert rules: trigger a callback when a log line matches a threshold condition."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class AlertRule:
    name: str
    pattern: re.Pattern
    threshold: int          # number of matches within window to trigger
    window: float           # seconds
    _hits: List[float] = field(default_factory=list, repr=False)

    def record_hit(self, now: Optional[float] = None) -> bool:
        """Record a match hit. Returns True if the alert threshold is reached."""
        now = now if now is not None else time.monotonic()
        cutoff = now - self.window
        self._hits = [t for t in self._hits if t >= cutoff]
        self._hits.append(now)
        return len(self._hits) >= self.threshold

    def reset(self) -> None:
        """Clear recorded hits."""
        self._hits.clear()


def parse_alert_rules(
    specs: Optional[str],
    threshold: int = 1,
    window: float = 60.0,
) -> List[AlertRule]:
    """Parse a comma-separated list of 'name:pattern' alert rule specs.

    Example: ``error:ERROR,warn:WARN``
    """
    if not specs:
        return []
    rules: List[AlertRule] = []
    for part in specs.split(","):
        part = part.strip()
        if ":" not in part:
            raise ValueError(f"Alert rule must be 'name:pattern', got: {part!r}")
        name, _, pattern_str = part.partition(":")
        name = name.strip()
        pattern_str = pattern_str.strip()
        if not name or not pattern_str:
            raise ValueError(f"Alert rule has empty name or pattern: {part!r}")
        rules.append(
            AlertRule(
                name=name,
                pattern=re.compile(pattern_str),
                threshold=threshold,
                window=window,
            )
        )
    return rules


def check_alerts(
    line: str,
    rules: List[AlertRule],
    callback: Callable[[AlertRule, str], None],
    now: Optional[float] = None,
) -> None:
    """Check *line* against every rule; invoke *callback* when a rule fires."""
    for rule in rules:
        if rule.pattern.search(line):
            if rule.record_hit(now=now):
                callback(rule, line)
