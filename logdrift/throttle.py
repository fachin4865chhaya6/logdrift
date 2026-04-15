"""Rate-limiting / throttle support for logdrift output.

Allows the caller to cap how many lines are emitted per second so that
high-volume log streams do not overwhelm a terminal or downstream sink.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


class Throttle:
    """Token-bucket style line-rate limiter.

    Parameters
    ----------
    max_lines_per_second:
        Maximum number of lines to allow through per second.  A value of
        ``0`` (or ``None``) disables throttling entirely.
    """

    def __init__(self, max_lines_per_second: float = 0) -> None:
        if max_lines_per_second < 0:
            raise ValueError("max_lines_per_second must be >= 0")
        self.max_lines_per_second: float = max_lines_per_second
        self._timestamps: Deque[float] = deque()

    @property
    def enabled(self) -> bool:
        return self.max_lines_per_second > 0

    def allow(self) -> bool:
        """Return *True* if the line should be emitted, *False* if it should
        be dropped to stay within the configured rate limit."""
        if not self.enabled:
            return True

        now = time.monotonic()
        window_start = now - 1.0

        # evict timestamps outside the 1-second sliding window
        while self._timestamps and self._timestamps[0] < window_start:
            self._timestamps.popleft()

        if len(self._timestamps) < self.max_lines_per_second:
            self._timestamps.append(now)
            return True

        return False

    def reset(self) -> None:
        """Clear internal state (useful in tests)."""
        self._timestamps.clear()


def parse_throttle_rate(value: Optional[str]) -> float:
    """Parse a CLI string such as ``'100'`` into a float rate.

    Returns ``0.0`` (disabled) when *value* is ``None`` or empty.
    Raises ``ValueError`` for non-numeric or negative values.
    """
    if not value:
        return 0.0
    try:
        rate = float(value)
    except ValueError:
        raise ValueError(f"Invalid throttle rate: {value!r}. Must be a number.")
    if rate < 0:
        raise ValueError(f"Throttle rate must be >= 0, got {rate}")
    return rate


def make_throttle(rate: float) -> Throttle:
    """Convenience factory that always returns a :class:`Throttle` instance."""
    return Throttle(max_lines_per_second=rate)
