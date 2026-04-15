"""Tests for logdrift.splitter."""

import json
import pytest

from logdrift.splitter import (
    LineSplitter,
    make_splitter,
    parse_split_field,
    write_split_summary,
)


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# parse_split_field
# ---------------------------------------------------------------------------

class TestParseSplitField:
    def test_valid_field_returned(self):
        assert parse_split_field("level") == "level"

    def test_strips_whitespace(self):
        assert parse_split_field("  service  ") == "service"

    def test_none_raises(self):
        with pytest.raises(ValueError):
            parse_split_field(None)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_split_field("")

    def test_blank_string_raises(self):
        with pytest.raises(ValueError):
            parse_split_field("   ")


# ---------------------------------------------------------------------------
# LineSplitter
# ---------------------------------------------------------------------------

class TestLineSplitter:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            LineSplitter("")

    def test_add_returns_bucket_key(self):
        s = LineSplitter("level")
        key = s.add(_line(level="info", msg="hello"))
        assert key == "info"

    def test_add_plain_text_returns_none(self):
        s = LineSplitter("level")
        key = s.add("not json at all")
        assert key is None

    def test_add_missing_field_returns_none(self):
        s = LineSplitter("level")
        key = s.add(_line(msg="no level here"))
        assert key is None

    def test_lines_grouped_by_field_value(self):
        s = LineSplitter("level")
        s.add(_line(level="info", msg="a"))
        s.add(_line(level="error", msg="b"))
        s.add(_line(level="info", msg="c"))
        assert len(s.buckets["info"]) == 2
        assert len(s.buckets["error"]) == 1

    def test_unmatched_lines_collected(self):
        s = LineSplitter("level")
        s.add("plain text")
        s.add(_line(msg="no level"))
        assert len(s.unmatched) == 2

    def test_reset_clears_buckets_and_unmatched(self):
        s = LineSplitter("level")
        s.add(_line(level="info"))
        s.add("plain")
        s.reset()
        assert s.buckets == {}
        assert s.unmatched == []

    def test_numeric_field_value_becomes_string_key(self):
        s = LineSplitter("code")
        key = s.add(_line(code=200))
        assert key == "200"
        assert "200" in s.buckets


# ---------------------------------------------------------------------------
# make_splitter
# ---------------------------------------------------------------------------

class TestMakeSplitter:
    def test_returns_none_for_none(self):
        assert make_splitter(None) is None

    def test_returns_none_for_empty_string(self):
        assert make_splitter("") is None

    def test_returns_splitter_for_valid_field(self):
        s = make_splitter("level")
        assert isinstance(s, LineSplitter)
        assert s.field == "level"


# ---------------------------------------------------------------------------
# write_split_summary
# ---------------------------------------------------------------------------

class TestWriteSplitSummary:
    def test_callback_called_per_bucket(self):
        s = LineSplitter("level")
        s.add(_line(level="info"))
        s.add(_line(level="error"))
        s.add(_line(level="info"))

        calls = []
        write_split_summary(s, lambda f, k, lines: calls.append((f, k, len(lines))))

        assert len(calls) == 2
        assert ("level", "info", 2) in calls
        assert ("level", "error", 1) in calls

    def test_no_callback_when_empty(self):
        s = LineSplitter("level")
        calls = []
        write_split_summary(s, lambda f, k, lines: calls.append(k))
        assert calls == []
