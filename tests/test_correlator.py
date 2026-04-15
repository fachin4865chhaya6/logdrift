"""Tests for logdrift.correlator."""

import json
import pytest

from logdrift.correlator import Correlator, parse_corr_field


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestCorrelator:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="corr_field"):
            Correlator(corr_field="")

    def test_non_positive_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            Correlator(corr_field="request_id", window_seconds=0)

    def test_add_plain_text_returns_none(self):
        c = Correlator(corr_field="request_id")
        assert c.add("not json") is None

    def test_add_missing_field_returns_none(self):
        c = Correlator(corr_field="request_id")
        assert c.add(_line(level="info", msg="hello")) is None

    def test_add_returns_key(self):
        c = Correlator(corr_field="request_id")
        key = c.add(_line(request_id="abc-123", msg="start"))
        assert key == "abc-123"

    def test_group_size_increments(self):
        c = Correlator(corr_field="request_id")
        c.add(_line(request_id="abc", msg="a"), now=1.0)
        c.add(_line(request_id="abc", msg="b"), now=2.0)
        assert c.group_size("abc") == 2

    def test_get_group_returns_parsed_lines(self):
        c = Correlator(corr_field="request_id")
        c.add(_line(request_id="x", msg="first"), now=1.0)
        group = c.get_group("x")
        assert len(group) == 1
        assert group[0]["msg"] == "first"

    def test_different_keys_bucketed_separately(self):
        c = Correlator(corr_field="request_id")
        c.add(_line(request_id="aaa", msg="one"), now=1.0)
        c.add(_line(request_id="bbb", msg="two"), now=1.0)
        assert c.group_size("aaa") == 1
        assert c.group_size("bbb") == 1

    def test_keys_lists_all_buckets(self):
        c = Correlator(corr_field="request_id")
        c.add(_line(request_id="p"), now=1.0)
        c.add(_line(request_id="q"), now=1.0)
        assert set(c.keys()) == {"p", "q"}

    def test_evicts_expired_entries(self):
        c = Correlator(corr_field="request_id", window_seconds=10.0)
        c.add(_line(request_id="old", msg="x"), now=0.0)
        c.add(_line(request_id="new", msg="y"), now=100.0)
        assert "old" not in c.keys()
        assert "new" in c.keys()

    def test_reset_clears_all_buckets(self):
        c = Correlator(corr_field="request_id")
        c.add(_line(request_id="z"), now=1.0)
        c.reset()
        assert c.keys() == []

    def test_unknown_key_returns_empty_group(self):
        c = Correlator(corr_field="request_id")
        assert c.get_group("nonexistent") == []


class TestParseCorrField:
    def test_none_returns_none(self):
        assert parse_corr_field(None) is None

    def test_empty_string_returns_none(self):
        assert parse_corr_field("") is None

    def test_whitespace_only_returns_none(self):
        assert parse_corr_field("   ") is None

    def test_valid_field_returned(self):
        assert parse_corr_field("request_id") == "request_id"

    def test_strips_whitespace(self):
        assert parse_corr_field("  trace_id  ") == "trace_id"
