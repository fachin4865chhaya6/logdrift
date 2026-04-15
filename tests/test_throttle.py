"""Tests for logdrift.throttle."""

from __future__ import annotations

import time
import pytest

from logdrift.throttle import Throttle, make_throttle, parse_throttle_rate


class TestThrottle:
    def test_disabled_when_rate_is_zero(self):
        t = Throttle(0)
        assert not t.enabled

    def test_enabled_when_rate_is_positive(self):
        t = Throttle(10)
        assert t.enabled

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            Throttle(-1)

    def test_disabled_throttle_always_allows(self):
        t = Throttle(0)
        for _ in range(1000):
            assert t.allow() is True

    def test_rate_1_allows_first_line(self):
        t = Throttle(1)
        assert t.allow() is True

    def test_rate_1_blocks_second_line_immediately(self):
        t = Throttle(1)
        t.allow()  # consume the single token
        assert t.allow() is False

    def test_rate_5_allows_five_lines(self):
        t = Throttle(5)
        results = [t.allow() for _ in range(5)]
        assert all(results)

    def test_rate_5_blocks_sixth_line(self):
        t = Throttle(5)
        for _ in range(5):
            t.allow()
        assert t.allow() is False

    def test_reset_clears_state(self):
        t = Throttle(1)
        t.allow()  # exhaust quota
        t.reset()
        assert t.allow() is True

    def test_tokens_replenish_after_window(self):
        t = Throttle(1)
        t.allow()  # consume token
        # Manually push the recorded timestamp outside the 1-second window
        t._timestamps[0] = time.monotonic() - 1.1
        assert t.allow() is True


class TestParseThrottleRate:
    def test_none_returns_zero(self):
        assert parse_throttle_rate(None) == 0.0

    def test_empty_string_returns_zero(self):
        assert parse_throttle_rate("") == 0.0

    def test_valid_integer_string(self):
        assert parse_throttle_rate("100") == 100.0

    def test_valid_float_string(self):
        assert parse_throttle_rate("2.5") == 2.5

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid throttle rate"):
            parse_throttle_rate("fast")

    def test_negative_string_raises(self):
        with pytest.raises(ValueError, match=">= 0"):
            parse_throttle_rate("-1")


class TestMakeThrottle:
    def test_returns_throttle_instance(self):
        t = make_throttle(50.0)
        assert isinstance(t, Throttle)
        assert t.max_lines_per_second == 50.0

    def test_zero_rate_disabled(self):
        t = make_throttle(0.0)
        assert not t.enabled
