"""Tests for logdrift.anomaly."""

import pytest

from logdrift.anomaly import AnomalyDetector, parse_anomaly_detector


class TestAnomalyDetector:
    def _det(self, threshold=5.0, window=10.0, cooldown=0.0):
        return AnomalyDetector(threshold=threshold, window_seconds=window, cooldown_seconds=cooldown)

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            AnomalyDetector(threshold=0, window_seconds=10)

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            AnomalyDetector(threshold=5, window_seconds=0)

    def test_negative_cooldown_raises(self):
        with pytest.raises(ValueError, match="cooldown"):
            AnomalyDetector(threshold=5, window_seconds=10, cooldown_seconds=-1)

    def test_initial_rate_is_zero(self):
        det = self._det()
        assert det.current_rate(now=0.0) == 0.0

    def test_rate_reflects_recorded_lines(self):
        det = self._det(threshold=5.0, window=10.0)
        for i in range(10):
            det.record(ts=float(i))
        # at ts=9.0, window covers [0,9], but ts=0 is evicted (< 9-10=-1 is fine)
        rate = det.current_rate(now=9.0)
        assert rate == pytest.approx(10 / 10.0)

    def test_old_entries_evicted(self):
        det = self._det(threshold=5.0, window=5.0)
        for i in range(5):
            det.record(ts=float(i))   # ts 0..4
        # advance to ts=10; all entries older than 10-5=5 are evicted
        rate = det.current_rate(now=10.0)
        assert rate == 0.0

    def test_below_threshold_not_anomalous(self):
        det = self._det(threshold=10.0, window=10.0)
        for i in range(5):
            det.record(ts=float(i))
        assert det.is_anomalous(now=5.0) is False

    def test_above_threshold_is_anomalous(self):
        det = self._det(threshold=2.0, window=10.0, cooldown=0.0)
        for i in range(50):
            det.record(ts=float(i) * 0.1)
        assert det.is_anomalous(now=5.0) is True

    def test_cooldown_suppresses_repeated_alerts(self):
        det = self._det(threshold=2.0, window=10.0, cooldown=30.0)
        for i in range(50):
            det.record(ts=float(i) * 0.1)
        assert det.is_anomalous(now=5.0) is True
        # second call within cooldown window should be suppressed
        assert det.is_anomalous(now=6.0) is False

    def test_alert_fires_again_after_cooldown(self):
        det = self._det(threshold=2.0, window=10.0, cooldown=5.0)
        for i in range(50):
            det.record(ts=float(i) * 0.1)
        assert det.is_anomalous(now=5.0) is True
        assert det.is_anomalous(now=11.0) is True

    def test_reset_clears_state(self):
        det = self._det(threshold=2.0, window=10.0, cooldown=0.0)
        for i in range(50):
            det.record(ts=float(i) * 0.1)
        det.reset()
        assert det.current_rate(now=10.0) == 0.0
        assert det.is_anomalous(now=10.0) is False


class TestParseAnomalyDetector:
    def test_none_threshold_returns_none(self):
        assert parse_anomaly_detector(None, None) is None

    def test_empty_threshold_returns_none(self):
        assert parse_anomaly_detector("", None) is None

    def test_valid_threshold_returns_detector(self):
        det = parse_anomaly_detector("10", None)
        assert det is not None
        assert det.threshold == 10.0
        assert det.window_seconds == 10.0

    def test_custom_window_applied(self):
        det = parse_anomaly_detector("5", "30")
        assert det is not None
        assert det.window_seconds == 30.0
