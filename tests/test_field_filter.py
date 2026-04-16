"""Tests for logdrift.field_filter."""
import json
import pytest

from logdrift.field_filter import FieldFilter, parse_field_filter_args, _parse_kv


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestParseKv:
    def test_none_returns_empty(self):
        assert _parse_kv(None) == {}

    def test_empty_string_returns_empty(self):
        assert _parse_kv("") == {}

    def test_single_pair(self):
        assert _parse_kv("level=error") == {"level": "error"}

    def test_multiple_pairs(self):
        assert _parse_kv("level=error,service=api") == {"level": "error", "service": "api"}

    def test_invalid_expression_raises(self):
        with pytest.raises(ValueError, match="Invalid field filter"):
            _parse_kv("nodot")


class TestFieldFilter:
    def test_plain_text_always_passes(self):
        ff = FieldFilter(include={"level": "error"})
        assert ff.passes("plain log line") is True

    def test_include_match_passes(self):
        ff = FieldFilter(include={"level": "error"})
        assert ff.passes(_line(level="error", msg="boom")) is True

    def test_include_no_match_fails(self):
        ff = FieldFilter(include={"level": "error"})
        assert ff.passes(_line(level="info", msg="ok")) is False

    def test_exclude_match_fails(self):
        ff = FieldFilter(exclude={"level": "debug"})
        assert ff.passes(_line(level="debug", msg="verbose")) is False

    def test_exclude_no_match_passes(self):
        ff = FieldFilter(exclude={"level": "debug"})
        assert ff.passes(_line(level="error", msg="boom")) is True

    def test_include_and_exclude_both_satisfied(self):
        ff = FieldFilter(include={"level": "error"}, exclude={"service": "worker"})
        assert ff.passes(_line(level="error", service="api")) is True

    def test_include_satisfied_but_exclude_blocks(self):
        ff = FieldFilter(include={"level": "error"}, exclude={"service": "worker"})
        assert ff.passes(_line(level="error", service="worker")) is False

    def test_nested_path(self):
        ff = FieldFilter(include={"meta.env": "prod"})
        line = json.dumps({"meta": {"env": "prod"}, "msg": "hi"})
        assert ff.passes(line) is True

    def test_missing_field_treated_as_none_string(self):
        ff = FieldFilter(include={"level": "None"})
        assert ff.passes(_line(msg="no level here")) is True


class TestParseFieldFilterArgs:
    def test_both_none(self):
        ff = parse_field_filter_args(None, None)
        assert ff.include == {}
        assert ff.exclude == {}

    def test_include_parsed(self):
        ff = parse_field_filter_args("level=error", None)
        assert ff.include == {"level": "error"}

    def test_exclude_parsed(self):
        ff = parse_field_filter_args(None, "level=debug")
        assert ff.exclude == {"level": "debug"}
