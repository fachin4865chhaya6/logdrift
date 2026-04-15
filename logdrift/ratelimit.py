"""Rate limiter that restricts how many lines are emitted per time window."""

import time
from typing import Optional


class RateLimiter:
    """Allows at most `max_lines` lines through per `window_seconds` window."""

    def __init__(self, max_lines: int, window_seconds: float = 1.0) -> None:
        if max_lines < 0:
            raise ValueError("max_lines must be >= 0")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self.max_lines = max_lines
        self.window_seconds = window_seconds
        self._window_start: float = time.monotonic()
        self._count: int = 0

    @property
    def enabled(self) -> bool:
        return self.max_lines > 0

    def allow(self, now: Optional[float] = None) -> bool:
        """Return True if the line should be emitted, False if rate-limited."""
        if not self.enabled:
            return True

        ts = now if now is not None else time.monotonic()

        if ts - self._window_start >= self.window_seconds:
            self._window_start = ts
            self._count = 0

        if self._count < self.max_lines:
            self._count += 1
            return True

        return False

    def reset(self, now: Optional[float] = None) -> None:
        """Manually reset the current window."""
        self._window_start = now if now is not None else time.monotonic()
        self._count = 0


def parse_rate_limit(value: Optional[str]) -> int:
    """Parse a rate-limit string (e.g. '100') into an integer.

    Returns 0 (disabled) when *value* is None or empty.
    Raises ValueError for non-integer or negative values.
    """
    if not value:
        return 0
    try:
        n = int(value)
    except ValueError:
        raise ValueError(f"Invalid rate limit value: {value!r}")
    if n < 0:
        raise ValueError("Rate limit must be >= 0")
    return n


def make_rate_limiter(
    max_lines: int, window_seconds: float = 1.0
) -> RateLimiter:
    """Factory that returns a RateLimiter (disabled when max_lines == 0)."""
    return RateLimiter(max_lines=max_lines, window_seconds=window_seconds)
