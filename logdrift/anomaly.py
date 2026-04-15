"""Anomaly detection for log line rates using a rolling window."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional


@dataclass
class AnomalyDetector:
    """Detects anomalies when the log line rate exceeds a threshold."""

    threshold: float          # max lines per second before anomaly fires
    window_seconds: float     # rolling window size in seconds
    _timestamps: Deque[float] = field(default_factory=deque, init=False)
    _last_alert_at: Optional[float] = field(default=None, init=False)
    cooldown_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")

    def record(self, ts: Optional[float] = None) -> None:
        """Record a new log line at the given timestamp (default: now)."""
        now = ts if ts is not None else time.monotonic()
        self._timestamps.append(now)
        self._evict(now)

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def current_rate(self, now: Optional[float] = None) -> float:
        """Return the current rate in lines/second over the rolling window."""
        t = now if now is not None else time.monotonic()
        self._evict(t)
        if self.window_seconds == 0:
            return 0.0
        return len(self._timestamps) / self.window_seconds

    def is_anomalous(self, now: Optional[float] = None) -> bool:
        """Return True when the current rate exceeds the threshold."""
        t = now if now is not None else time.monotonic()
        if self.current_rate(t) <= self.threshold:
            return False
        if self._last_alert_at is not None and (t - self._last_alert_at) < self.cooldown_seconds:
            return False
        self._last_alert_at = t
        return True

    def reset(self) -> None:
        self._timestamps.clear()
        self._last_alert_at = None


def parse_anomaly_detector(threshold_str: Optional[str], window_str: Optional[str]) -> Optional[AnomalyDetector]:
    """Build an AnomalyDetector from CLI string arguments, or return None."""
    if not threshold_str:
        return None
    threshold = float(threshold_str)
    window = float(window_str) if window_str else 10.0
    return AnomalyDetector(threshold=threshold, window_seconds=window)
