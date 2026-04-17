"""Tests for logdrift.differ."""
import json
import pytest
from logdrift.differ import LineDiffer, parse_diff_fields


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestParseDiffFields:
    def test_none_returns_empty(self):
        assert parse_diff_fields(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_diff_fields("") == []

    def test_single_field(self):
        assert parse_diff_fields("level") == ["level"]

    def test_multiple_fields(self):
        assert parse_diff_fields("level,status") == ["level", "status"]

    def test_strips_whitespace(self):
        assert parse_diff_fields(" level , status ") == ["level", "status"]


class TestLineDiffer:
    def test_empty_fields_raises(self):
        with pytest.raises(ValueError):
            LineDiffer(fields=[])

    def test_plain_text_returns_none(self):
        d = LineDiffer(fields=["level"])
        assert d.diff("not json") is None

    def test_first_line_all_fields_changed_from_none(self):
        d = LineDiffer(fields=["level"])
        result = d.diff(_line(level="info"))
        assert result == {"level": (None, "info")}

    def test_unchanged_field_not_in_result(self):
        d = LineDiffer(fields=["level"])
        d.diff(_line(level="info"))
        result = d.diff(_line(level="info"))
        assert result == {}

    def test_changed_field_in_result(self):
        d = LineDiffer(fields=["level"])
        d.diff(_line(level="info"))
        result = d.diff(_line(level="error"))
        assert result == {"level": ("info", "error")}

    def test_multiple_fields_partial_change(self):
        d = LineDiffer(fields=["level", "status"])
        d.diff(_line(level="info", status=200))
        result = d.diff(_line(level="info", status=500))
        assert "level" not in result
        assert result["status"] == (200, 500)

    def test_total_counts_json_lines(self):
        d = LineDiffer(fields=["level"])
        d.diff(_line(level="info"))
        d.diff("plain")
        d.diff(_line(level="error"))
        assert d.total == 2

    def test_changes_counts_diffed_lines(self):
        d = LineDiffer(fields=["level"])
        d.diff(_line(level="info"))
        d.diff(_line(level="info"))
        d.diff(_line(level="error"))
        assert d.changes == 2

    def test_format_diff_empty(self):
        d = LineDiffer(fields=["level"])
        assert d.format_diff({}) == ""

    def test_format_diff_nonempty(self):
        d = LineDiffer(fields=["level"])
        out = d.format_diff({"level": ("info", "error")})
        assert "[diff]" in out
        assert "level" in out

    def test_reset_clears_state(self):
        d = LineDiffer(fields=["level"])
        d.diff(_line(level="info"))
        d.reset()
        assert d.total == 0
        assert d.changes == 0
        result = d.diff(_line(level="info"))
        assert result == {"level": (None, "info")}
