"""Tests for logdrift.clipper."""
from __future__ import annotations

import json

import pytest

from logdrift.clipper import (
    ClipRule,
    clip_json_fields,
    clip_line,
    parse_clip_rules,
)


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# ClipRule construction
# ---------------------------------------------------------------------------

class TestClipRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            ClipRule(field="", max_length=10)

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            ClipRule(field="   ", max_length=10)

    def test_zero_max_length_raises(self):
        with pytest.raises(ValueError, match="max_length"):
            ClipRule(field="msg", max_length=0)

    def test_negative_max_length_raises(self):
        with pytest.raises(ValueError, match="max_length"):
            ClipRule(field="msg", max_length=-5)

    def test_apply_short_string_unchanged(self):
        rule = ClipRule(field="msg", max_length=20)
        assert rule.apply("hello") == "hello"

    def test_apply_exact_length_unchanged(self):
        rule = ClipRule(field="msg", max_length=5)
        assert rule.apply("hello") == "hello"

    def test_apply_long_string_clipped(self):
        rule = ClipRule(field="msg", max_length=5)
        assert rule.apply("hello world") == "hello..."

    def test_apply_custom_suffix(self):
        rule = ClipRule(field="msg", max_length=4, suffix="~")
        assert rule.apply("abcdefgh") == "abcd~"

    def test_apply_non_string_unchanged(self):
        rule = ClipRule(field="count", max_length=3)
        assert rule.apply(42) == 42

    def test_apply_none_unchanged(self):
        rule = ClipRule(field="msg", max_length=5)
        assert rule.apply(None) is None


# ---------------------------------------------------------------------------
# parse_clip_rules
# ---------------------------------------------------------------------------

def test_none_returns_empty():
    assert parse_clip_rules(None) == []


def test_empty_string_returns_empty():
    assert parse_clip_rules("") == []


def test_whitespace_returns_empty():
    assert parse_clip_rules("   ") == []


def test_single_rule():
    rules = parse_clip_rules("message:80")
    assert len(rules) == 1
    assert rules[0].field == "message"
    assert rules[0].max_length == 80
    assert rules[0].suffix == "..."


def test_multiple_rules():
    rules = parse_clip_rules("message:80,reason:40")
    assert len(rules) == 2
    assert rules[1].field == "reason"
    assert rules[1].max_length == 40


def test_custom_suffix_in_spec():
    rules = parse_clip_rules("msg:10:>>")
    assert rules[0].suffix == ">>"


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        parse_clip_rules("message")


def test_non_integer_max_length_raises():
    with pytest.raises(ValueError):
        parse_clip_rules("message:abc")


# ---------------------------------------------------------------------------
# clip_json_fields
# ---------------------------------------------------------------------------

def test_no_rules_returns_data_unchanged():
    data = {"msg": "hello"}
    assert clip_json_fields(data, []) is data


def test_clips_matching_field():
    data = {"msg": "hello world"}
    rules = [ClipRule(field="msg", max_length=5)]
    result = clip_json_fields(data, rules)
    assert result["msg"] == "hello..."


def test_ignores_missing_field():
    data = {"other": "value"}
    rules = [ClipRule(field="msg", max_length=5)]
    result = clip_json_fields(data, rules)
    assert "msg" not in result


def test_does_not_mutate_original():
    data = {"msg": "hello world"}
    rules = [ClipRule(field="msg", max_length=5)]
    clip_json_fields(data, rules)
    assert data["msg"] == "hello world"


# ---------------------------------------------------------------------------
# clip_line
# ---------------------------------------------------------------------------

def test_plain_text_unchanged():
    rules = [ClipRule(field="msg", max_length=5)]
    assert clip_line("not json", rules) == "not json"


def test_json_line_clipped():
    raw = _line(message="this is a very long message that exceeds the limit")
    rules = [ClipRule(field="message", max_length=10)]
    result = clip_line(raw, rules)
    parsed = json.loads(result)
    assert parsed["message"] == "this is a ..." or parsed["message"].startswith("this is a")


def test_no_rules_line_unchanged():
    raw = _line(message="hello")
    assert clip_line(raw, []) == raw
