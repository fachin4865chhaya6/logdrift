"""Tests for logdrift.formatter module."""

import pytest
from logdrift.formatter import (
    colorize,
    format_line,
    get_log_level,
    ANSI_COLORS,
)


class TestColorize:
    def test_wraps_text_with_color_codes(self):
        result = colorize("hello", "red")
        assert ANSI_COLORS["red"] in result
        assert ANSI_COLORS["reset"] in result
        assert "hello" in result

    def test_unknown_color_returns_text_with_reset(self):
        result = colorize("hello", "ultraviolet")
        assert "hello" in result
        assert ANSI_COLORS["reset"] in result


class TestGetLogLevel:
    def test_extracts_level_key(self):
        assert get_log_level({"level": "INFO"}) == "info"

    def test_extracts_severity_key(self):
        assert get_log_level({"severity": "ERROR"}) == "error"

    def test_extracts_lvl_key(self):
        assert get_log_level({"lvl": "debug"}) == "debug"

    def test_returns_none_when_no_level_key(self):
        assert get_log_level({"message": "no level here"}) is None

    def test_level_key_takes_priority(self):
        result = get_log_level({"level": "warn", "severity": "error"})
        assert result == "warn"


class TestFormatLine:
    def test_returns_raw_line_when_parsed_is_none(self):
        result = format_line("plain text log", None)
        assert result == "plain text log"

    def test_colorizes_error_level_red(self):
        parsed = {"level": "error", "msg": "something broke"}
        raw = '{"level": "error", "msg": "something broke"}'
        result = format_line(raw, parsed, colorize_output=True)
        assert ANSI_COLORS["red"] in result

    def test_colorizes_info_level_green(self):
        parsed = {"level": "info", "msg": "all good"}
        raw = '{"level": "info", "msg": "all good"}'
        result = format_line(raw, parsed, colorize_output=True)
        assert ANSI_COLORS["green"] in result

    def test_no_color_returns_plain_text(self):
        parsed = {"level": "error", "msg": "oops"}
        raw = '{"level": "error", "msg": "oops"}'
        result = format_line(raw, parsed, colorize_output=False)
        assert result == raw
        assert ANSI_COLORS["red"] not in result

    def test_pretty_print_formats_json(self):
        parsed = {"level": "info", "msg": "hello"}
        raw = '{"level": "info", "msg": "hello"}'
        result = format_line(raw, parsed, colorize_output=False, pretty=True)
        assert "\n" in result
        assert "  " in result

    def test_unknown_level_uses_white_color(self):
        parsed = {"level": "trace", "msg": "verbose"}
        raw = '{"level": "trace", "msg": "verbose"}'
        result = format_line(raw, parsed, colorize_output=True)
        assert ANSI_COLORS["white"] in result
