"""Tests for logdrift.ratelimit."""

import pytest

from logdrift.ratelimit import RateLimiter, make_rate_limiter, parse_rate_limit


class TestRateLimiter:
    def test_disabled_when_max_lines_zero(self):
        rl = RateLimiter(max_lines=0)
        assert rl.enabled is False

    def test_enabled_when_max_lines_positive(self):
        rl = RateLimiter(max_lines=5)
        assert rl.enabled is True

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            RateLimiter(max_lines=-1)

    def test_non_positive_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateLimiter(max_lines=10, window_seconds=0)

    def test_disabled_always_allows(self):
        rl = RateLimiter(max_lines=0)
        for _ in range(1000):
            assert rl.allow() is True

    def test_allows_up_to_max_lines_in_window(self):
        rl = RateLimiter(max_lines=3, window_seconds=60.0)
        t = 0.0
        assert rl.allow(now=t) is True
        assert rl.allow(now=t) is True
        assert rl.allow(now=t) is True
        assert rl.allow(now=t) is False

    def test_rejects_beyond_max_lines(self):
        rl = RateLimiter(max_lines=2, window_seconds=60.0)
        t = 0.0
        rl.allow(now=t)
        rl.allow(now=t)
        assert rl.allow(now=t) is False
        assert rl.allow(now=t) is False

    def test_window_reset_allows_new_lines(self):
        rl = RateLimiter(max_lines=2, window_seconds=1.0)
        t = 0.0
        rl.allow(now=t)
        rl.allow(now=t)
        assert rl.allow(now=t) is False
        # advance past the window
        t2 = 2.0
        assert rl.allow(now=t2) is True
        assert rl.allow(now=t2) is True
        assert rl.allow(now=t2) is False

    def test_reset_clears_count(self):
        rl = RateLimiter(max_lines=1, window_seconds=60.0)
        t = 0.0
        rl.allow(now=t)
        assert rl.allow(now=t) is False
        rl.reset(now=t)
        assert rl.allow(now=t) is True

    def test_reset_uses_monotonic_when_no_arg(self):
        rl = RateLimiter(max_lines=1, window_seconds=60.0)
        rl.allow()
        rl.reset()
        assert rl.allow() is True


class TestParseRateLimit:
    def test_none_returns_zero(self):
        assert parse_rate_limit(None) == 0

    def test_empty_string_returns_zero(self):
        assert parse_rate_limit("") == 0

    def test_valid_integer_string(self):
        assert parse_rate_limit("100") == 100

    def test_zero_string(self):
        assert parse_rate_limit("0") == 0

    def test_non_integer_raises(self):
        with pytest.raises(ValueError, match="Invalid rate limit"):
            parse_rate_limit("fast")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match=">= 0"):
            parse_rate_limit("-5")


class TestMakeRateLimiter:
    def test_returns_rate_limiter_instance(self):
        rl = make_rate_limiter(10)
        assert isinstance(rl, RateLimiter)

    def test_disabled_when_zero(self):
        rl = make_rate_limiter(0)
        assert rl.enabled is False

    def test_custom_window(self):
        rl = make_rate_limiter(5, window_seconds=30.0)
        assert rl.window_seconds == 30.0
