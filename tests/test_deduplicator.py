"""Tests for logdrift.deduplicator."""

import time
import pytest
from unittest.mock import patch

from logdrift.deduplicator import (
    Deduplicator,
    parse_dedup_window,
    make_deduplicator,
)


class TestDeduplicator:
    def test_first_occurrence_not_duplicate(self):
        d = Deduplicator(window_seconds=5.0)
        assert d.is_duplicate("hello world") is False

    def test_second_occurrence_is_duplicate(self):
        d = Deduplicator(window_seconds=5.0)
        d.is_duplicate("hello world")
        assert d.is_duplicate("hello world") is True

    def test_different_lines_not_duplicate(self):
        d = Deduplicator(window_seconds=5.0)
        d.is_duplicate("line one")
        assert d.is_duplicate("line two") is False

    def test_line_not_duplicate_after_window_expires(self):
        d = Deduplicator(window_.0)
        start = 100.0
        with patch("logdrift.deduplicator.time.monotonic", return_value=start):
            d.is_duplicate("expiring line")
        with patch("logdrift.deduplicator.time.monotonic", return_value=start + 2.0):
            assert d.is_duplicate("expiring line") is False

    def test_line_still_duplicate_within_window(self):
        d = Deduplicator(window_seconds=10.0)
        start = 100.0
        with patch("logdrift.deduplicator.time.monotonic", return_value=start):
            d.is_duplicate("persistent line")
        with patch("logdrift.deduplicator.time.monotonic", return_value=start + 5.0):
            assert d.is_duplicate("persistent line") is True

    def test_reset_clears_cache(self):
        d = Deduplicator(window_seconds=5.0)
        d.is_duplicate("some line")
        d.reset()
        assert d.is_duplicate("some line") is False

    def test_max_cache_size_evicts_oldest(self):
        d = Deduplicator(window_seconds=60.0, max_cache_size=3)
        t = 100.0
        for i in range(3):
            with patch("logdrift.deduplicator.time.monotonic", return_value=t + i):
                d.is_duplicate(f"line {i}")
        with patch("logdrift.deduplicator.time.monotonic", return_value=t + 10):
            d.is_duplicate("overflow line")
        assert len(d._seen) == 3

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            Deduplicator(window_seconds=-1.0)

    def test_invalid_cache_size_raises(self):
        with pytest.raises(ValueError):
            Deduplicator(max_cache_size=0)


class TestParseDedupWindow:
    def test_none_returns_none(self):
        assert parse_dedup_window(None) is None

    def test_empty_string_returns_none(self):
        assert parse_dedup_window("") is None

    def test_valid_integer_string(self):
        assert parse_dedup_window("5") == 5.0

    def test_valid_float_string(self):
        assert parse_dedup_window("2.5") == 2.5

    def test_zero_is_valid(self):
        assert parse_dedup_window("0") == 0.0

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            parse_dedup_window("-1")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid dedup window"):
            parse_dedup_window("fast")


class TestMakeDeduplicator:
    def test_none_returns_none(self):
        assert make_deduplicator(None) is None

    def test_returns_deduplicator_instance(self):
        result = make_deduplicator(3.0)
        assert isinstance(result, Deduplicator)
        assert result.window_seconds == 3.0
