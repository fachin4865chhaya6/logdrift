"""Tests for logdrift.formatter_field."""
from __future__ import annotations

import json
import pytest

from logdrift.formatter_field import (
    FormatRule,
    parse_format_rules,
    format_json_fields,
    format_line,
)


def _line(**kw) -> str:
    return json.dumps(kw)


# ---------------------------------------------------------------------------
# FormatRule
# ---------------------------------------------------------------------------

class TestFormatRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            FormatRule(field="", fmt="{:.2f}")

    def test_empty_fmt_raises(self):
        with pytest.raises(ValueError, match="fmt"):
            FormatRule(field="latency", fmt="")

    def test_apply_float_format(self):
        rule = FormatRule(field="latency", fmt="{:.2f}")
        assert rule.apply(3.14159) == "3.14"

    def test_apply_width_format(self):
        rule = FormatRule(field="user", fmt="{:>10}")
        assert rule.apply("alice") == "     alice"

    def test_apply_bad_format_returns_str(self):
        rule = FormatRule(field="val", fmt="{:.2f}")
        # string passed to float format — should not raise
        result = rule.apply("not_a_float")
        assert result == "not_a_float"


# ---------------------------------------------------------------------------
# parse_format_rules
# ---------------------------------------------------------------------------

class TestParseFormatRules:
    def test_none_returns_empty(self):
        assert parse_format_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_format_rules("") == []

    def test_single_rule(self):
        rules = parse_format_rules("latency:{:.3f}")
        assert len(rules) == 1
        assert rules[0].field == "latency"
        assert rules[0].fmt == "{:.3f}"

    def test_multiple_rules(self):
        rules = parse_format_rules("latency:{:.2f},user:{:>12}")
        assert len(rules) == 2
        assert rules[0].field == "latency"
        assert rules[1].field == "user"

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError):
            parse_format_rules("latency")

    def test_whitespace_stripped(self):
        rules = parse_format_rules(" latency : {:.1f} ")
        assert rules[0].field == "latency"
        assert rules[0].fmt == "{:.1f}"


# ---------------------------------------------------------------------------
# format_json_fields
# ---------------------------------------------------------------------------

class TestFormatJsonFields:
    def test_no_rules_returns_same(self):
        data = {"latency": 1.23}
        assert format_json_fields(data, []) is data

    def test_applies_rule(self):
        data = {"latency": 3.14159}
        rules = [FormatRule(field="latency", fmt="{:.2f}")]
        result = format_json_fields(data, rules)
        assert result["latency"] == "3.14"

    def test_unrelated_field_unchanged(self):
        data = {"latency": 1.0, "user": "alice"}
        rules = [FormatRule(field="latency", fmt="{:.1f}")]
        result = format_json_fields(data, rules)
        assert result["user"] == "alice"

    def test_missing_field_skipped(self):
        data = {"user": "alice"}
        rules = [FormatRule(field="latency", fmt="{:.2f}")]
        result = format_json_fields(data, rules)
        assert "latency" not in result


# ---------------------------------------------------------------------------
# format_line
# ---------------------------------------------------------------------------

class TestFormatLine:
    def test_plain_text_unchanged(self):
        rules = [FormatRule(field="x", fmt="{:.2f}")]
        assert format_line("hello world", rules) == "hello world"

    def test_no_rules_unchanged(self):
        raw = _line(latency=3.14)
        assert format_line(raw, []) == raw

    def test_json_field_formatted(self):
        raw = _line(latency=3.14159)
        rules = [FormatRule(field="latency", fmt="{:.2f}")]
        result = json.loads(format_line(raw, rules))
        assert result["latency"] == "3.14"
