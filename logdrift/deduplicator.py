"""Deduplicator module for suppressing repeated log lines within a time window."""

import hashlib
import time
from typing import Optional


class Deduplicator:
    """Tracks recently seen log lines and suppresses duplicates within a window."""

    def __init__(self, window_seconds: float = 5.0, max_cache_size: int = 1000):
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")
        if max_cache_size < 1:
            raise ValueError("max_cache_size must be at least 1")
        self.window_seconds = window_seconds
        self.max_cache_size = max_cache_size
        self._seen: dict[str, float] = {}

    def _hash_line(self, line: str) -> str:
        return hashlib.md5(line.encode("utf-8")).hexdigest()

    def _evict_expired(self, now: float) -> None:
        expired = [k for k, ts in self._seen.items() if now - ts >= self.window_seconds]
        for k in expired:
            del self._seen[k]

    def is_duplicate(self, line: str) -> bool:
        """Return True if line was seen within the current window."""
        now = time.monotonic()
        self._evict_expired(now)

        key = self._hash_line(line)
        if key in self._seen:
            return True

        # Evict oldest entry if cache is full
        if len(self._seen) >= self.max_cache_size:
            oldest_key = min(self._seen, key=lambda k: self._seen[k])
            del self._seen[oldest_key]

        self._seen[key] = now
        return False

    def reset(self) -> None:
        """Clear all tracked lines."""
        self._seen.clear()


def parse_dedup_window(value: Optional[str]) -> Optional[float]:
    """Parse a dedup window string (e.g. '5', '2.5') into a float of seconds.

    Returns None if value is None or empty, indicating deduplication is disabled.
    """
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        raise ValueError(f"Invalid dedup window value: {value!r}. Expected a number of seconds.")
    if seconds < 0:
        raise ValueError(f"Dedup window must be non-negative, got {seconds}")
    return seconds


def make_deduplicator(window_seconds: Optional[float]) -> Optional[Deduplicator]:
    """Return a Deduplicator if window_seconds is set, otherwise None."""
    if window_seconds is None:
        return None
    return Deduplicator(window_seconds=window_seconds)
