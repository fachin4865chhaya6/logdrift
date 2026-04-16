"""Tests for logdrift.profiler."""
import json
import pytest
from logdrift.profiler import FieldProfiler, parse_profile_field, make_profiler


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestFieldProfiler:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            FieldProfiler(_field="")

    def test_limit_zero_raises(self):
        with pytest.raises(ValueError):
            FieldProfiler(_field="level", _limit=0)

    def test_add_plain_text_returns_none(self):
        p = FieldProfiler(_field="level")
        assert p.add("not json") is None

    def test_add_missing_field_returns_none(self):
        p = FieldProfiler(_field="level")
        assert p.add(_line(msg="hello")) is None

    def test_add_returns_value_key(self):
        p = FieldProfiler(_field="level")
        assert p.add(_line(level="info")) == "info"

    def test_total_increments(self):
        p = FieldProfiler(_field="level")
        p.add(_line(level="info"))
        p.add(_line(level="warn"))
        assert p.total == 2

    def test_missing_field_does_not_increment_total(self):
        p = FieldProfiler(_field="level")
        p.add(_line(msg="hi"))
        assert p.total == 0

    def test_top_returns_most_common(self):
        p = FieldProfiler(_field="level")
        for _ in range(3):
            p.add(_line(level="info"))
        p.add(_line(level="warn"))
        top = p.top()
        assert top[0] == ("info", 3)
        assert top[1] == ("warn", 1)

    def test_top_respects_limit(self):
        p = FieldProfiler(_field="level", _limit=2)
        for v in ["a", "b", "c", "a", "b", "a"]:
            p.add(_line(level=v))
        assert len(p.top()) == 2

    def test_format_summary_contains_field(self):
        p = FieldProfiler(_field="level")
        p.add(_line(level="info"))
        summary = p.format_summary()
        assert "level" in summary
        assert "info" in summary

    def test_format_summary_shows_percentage(self):
        p = FieldProfiler(_field="level")
        p.add(_line(level="info"))
        p.add(_line(level="info"))
        p.add(_line(level="warn"))
        summary = p.format_summary()
        assert "66.7%" in summary

    def test_format_summary_empty(self):
        p = FieldProfiler(_field="level")
        summary = p.format_summary()
        assert "0 values" in summary


class TestParseProfileField:
    def test_none_returns_none(self):
        assert parse_profile_field(None) is None

    def test_empty_returns_none(self):
        assert parse_profile_field("") is None

    def test_whitespace_returns_none(self):
        assert parse_profile_field("   ") is None

    def test_valid_field_stripped(self):
        assert parse_profile_field("  level  ") == "level"


class TestMakeProfiler:
    def test_none_returns_none(self):
        assert make_profiler(None) is None

    def test_empty_returns_none(self):
        assert make_profiler("") is None

    def test_returns_profiler(self):
        p = make_profiler("level")
        assert isinstance(p, FieldProfiler)
        assert p.field == "level"

    def test_limit_passed_through(self):
        p = make_profiler("level", limit=5)
        assert p._limit == 5
