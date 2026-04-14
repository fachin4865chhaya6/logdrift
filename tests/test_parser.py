"""Tests for logdrift.parser module."""

import pytest
from logdrift.parser import (
    filter_line,
    get_json_path_value,
    matches_json_filter,
    matches_regex_filter,
    parse_line,
)


class TestParseLine:
    def test_valid_json_object(self):
        line = '{"level": "ERROR", "msg": "disk full"}'
        result = parse_line(line)
        assert result == {"level": "ERROR", "msg": "disk full"}

    def test_plain_text_returns_none(self):
        assert parse_line("2024-01-01 ERROR something went wrong") is None

    def test_json_array_returns_none(self):
        assert parse_line('["a", "b"]') is None

    def test_empty_line_returns_none(self):
        assert parse_line("") is None
        assert parse_line("   ") is None


class TestGetJsonPathValue:
    def test_top_level_key(self):
        assert get_json_path_value({"level": "INFO"}, "level") == "INFO"

    def test_nested_key(self):
        data = {"request": {"method": "GET", "path": "/health"}}
        assert get_json_path_value(data, "request.method") == "GET"

    def test_missing_key_returns_none(self):
        assert get_json_path_value({"level": "INFO"}, "missing") is None

    def test_deeply_missing_path_returns_none(self):
        assert get_json_path_value({"a": {"b": 1}}, "a.c.d") is None


class TestMatchesJsonFilter:
    def test_matching_field(self):
        data = {"level": "ERROR"}
        assert matches_json_filter(data, "level", "ERROR") is True

    def test_non_matching_field(self):
        data = {"level": "INFO"}
        assert matches_json_filter(data, "level", "ERROR") is False

    def test_regex_partial_match(self):
        data = {"msg": "connection timeout occurred"}
        assert matches_json_filter(data, "msg", "timeout") is True

    def test_missing_path_returns_false(self):
        data = {"level": "INFO"}
        assert matches_json_filter(data, "request.method", "GET") is False


class TestMatchesRegexFilter:
    def test_simple_match(self):
        assert matches_regex_filter("ERROR: disk full", "ERROR") is True

    def test_no_match(self):
        assert matches_regex_filter("INFO: all good", "ERROR") is False

    def test_regex_pattern(self):
        assert matches_regex_filter("user_123 logged in", r"user_\d+") is True


class TestFilterLine:
    def test_no_filters_accepts_nonempty_line(self):
        assert filter_line("any log line") is True

    def test_empty_line_rejected(self):
        assert filter_line("") is False

    def test_regex_filter_match(self):
        assert filter_line("ERROR: something", regex="ERROR") is True

    def test_regex_filter_no_match(self):
        assert filter_line("INFO: something", regex="ERROR") is False

    def test_json_path_filter_match(self):
        line = '{"level": "WARN", "service": "api"}'
        assert filter_line(line, json_path="level", json_pattern="WARN") is True

    def test_json_path_filter_no_match(self):
        line = '{"level": "INFO", "service": "api"}'
        assert filter_line(line, json_path="level", json_pattern="ERROR") is False

    def test_json_path_filter_on_plain_text_rejected(self):
        line = "plain text log line"
        assert filter_line(line, json_path="level", json_pattern="ERROR") is False

    def test_combined_filters_both_pass(self):
        line = '{"level": "ERROR", "msg": "timeout"}'
        assert filter_line(line, regex="timeout", json_path="level", json_pattern="ERROR") is True

    def test_combined_filters_regex_fails(self):
        line = '{"level": "ERROR", "msg": "disk full"}'
        assert filter_line(line, regex="timeout", json_path="level", json_pattern="ERROR") is False
