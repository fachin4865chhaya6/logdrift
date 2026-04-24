"""Tests for logdrift.normalizer and logdrift.normalize_output."""
from __future__ import annotations

import json
import pytest

from logdrift.normalizer import (
    NormalizeRule,
    parse_normalize_rules,
    normalize_json_fields,
    normalize_line,
)
from logdrift.normalize_output import make_normalize_rules, apply_normalization


# ---------------------------------------------------------------------------
# NormalizeRule
# ---------------------------------------------------------------------------

class TestNormalizeRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field must not be empty"):
            NormalizeRule(field="", transform="lower")

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError, match="field must not be empty"):
            NormalizeRule(field="   ", transform="lower")

    def test_unsupported_transform_raises(self):
        with pytest.raises(ValueError, match="unsupported transform"):
            NormalizeRule(field="level", transform="kebab")

    def test_apply_lower(self):
        rule = NormalizeRule(field="level", transform="lower")
        assert rule.apply("ERROR") == "error"

    def test_apply_upper(self):
        rule = NormalizeRule(field="level", transform="upper")
        assert rule.apply("warn") == "WARN"

    def test_apply_strip(self):
        rule = NormalizeRule(field="msg", transform="strip")
        assert rule.apply("  hello  ") == "hello"

    def test_apply_title(self):
        rule = NormalizeRule(field="msg", transform="title")
        assert rule.apply("hello world") == "Hello World"

    def test_apply_non_string_unchanged(self):
        rule = NormalizeRule(field="count", transform="lower")
        assert rule.apply(42) == 42


# ---------------------------------------------------------------------------
# parse_normalize_rules
# ---------------------------------------------------------------------------

class TestParseNormalizeRules:
    def test_none_returns_empty(self):
        assert parse_normalize_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_normalize_rules("") == []

    def test_whitespace_returns_empty(self):
        assert parse_normalize_rules("   ") == []

    def test_single_rule(self):
        rules = parse_normalize_rules("level:lower")
        assert len(rules) == 1
        assert rules[0].field == "level"
        assert rules[0].transform == "lower"

    def test_multiple_rules(self):
        rules = parse_normalize_rules("level:upper,msg:strip")
        assert len(rules) == 2
        assert rules[1].field == "msg"

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="invalid normalize rule"):
            parse_normalize_rules("levelupper")

    def test_strips_whitespace_around_tokens(self):
        rules = parse_normalize_rules(" level : lower ")
        assert rules[0].field == "level"
        assert rules[0].transform == "lower"


# ---------------------------------------------------------------------------
# normalize_json_fields / normalize_line
# ---------------------------------------------------------------------------

def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_normalize_json_fields_applies_rule():
    rules = [NormalizeRule(field="level", transform="lower")]
    result = normalize_json_fields({"level": "ERROR", "msg": "hi"}, rules)
    assert result["level"] == "error"
    assert result["msg"] == "hi"


def test_normalize_json_fields_missing_field_unchanged():
    rules = [NormalizeRule(field="level", transform="lower")]
    data = {"msg": "hello"}
    result = normalize_json_fields(data, rules)
    assert result == data


def test_normalize_line_valid_json():
    raw = _line(level="WARN", msg="ok")
    rules = [NormalizeRule(field="level", transform="lower")]
    out = normalize_line(raw, rules)
    assert json.loads(out)["level"] == "warn"


def test_normalize_line_plain_text_unchanged():
    raw = "not json at all"
    rules = [NormalizeRule(field="level", transform="lower")]
    assert normalize_line(raw, rules) == raw


def test_normalize_line_json_array_unchanged():
    raw = json.dumps([1, 2, 3])
    rules = [NormalizeRule(field="level", transform="lower")]
    assert normalize_line(raw, rules) == raw


def test_normalize_line_no_rules_unchanged():
    raw = _line(level="ERROR")
    assert normalize_line(raw, []) == raw


# ---------------------------------------------------------------------------
# normalize_output helpers
# ---------------------------------------------------------------------------

def test_make_normalize_rules_none_returns_empty():
    assert make_normalize_rules(None) == []


def test_make_normalize_rules_returns_rules():
    rules = make_normalize_rules("level:lower")
    assert len(rules) == 1


def test_apply_normalization_no_rules_unchanged():
    raw = _line(level="ERROR")
    assert apply_normalization(raw, []) == raw


def test_apply_normalization_transforms_field():
    raw = _line(level="ERROR")
    rules = make_normalize_rules("level:lower")
    out = apply_normalization(raw, rules)
    assert json.loads(out)["level"] == "error"
