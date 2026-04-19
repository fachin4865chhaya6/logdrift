"""Tests for logdrift.capper and logdrift.cap_output."""
from __future__ import annotations

import json

import pytest

from logdrift.cap_output import apply_capping, make_cap_rules
from logdrift.capper import CapRule, cap_json_fields, cap_line, parse_cap_rules


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# CapRule
# ---------------------------------------------------------------------------
class TestCapRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            CapRule(field="", min_val=0, max_val=100)

    def test_no_bounds_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            CapRule(field="x", min_val=None, max_val=None)

    def test_min_greater_than_max_raises(self):
        with pytest.raises(ValueError, match="min_val"):
            CapRule(field="x", min_val=10, max_val=5)

    def test_apply_clamps_below_min(self):
        rule = CapRule(field="x", min_val=0.0, max_val=None)
        assert rule.apply(-5) == 0.0

    def test_apply_clamps_above_max(self):
        rule = CapRule(field="x", min_val=None, max_val=100.0)
        assert rule.apply(200) == 100.0

    def test_apply_within_range_unchanged(self):
        rule = CapRule(field="x", min_val=0.0, max_val=100.0)
        assert rule.apply(50) == 50

    def test_apply_at_boundary(self):
        rule = CapRule(field="x", min_val=10.0, max_val=10.0)
        assert rule.apply(10) == 10


# ---------------------------------------------------------------------------
# parse_cap_rules
# ---------------------------------------------------------------------------
class TestParseCapRules:
    def test_none_returns_empty(self):
        assert parse_cap_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_cap_rules("") == []

    def test_single_rule(self):
        rules = parse_cap_rules("latency:0:500")
        assert len(rules) == 1
        assert rules[0].field == "latency"
        assert rules[0].min_val == 0
        assert rules[0].max_val == 500

    def test_wildcard_min(self):
        rules = parse_cap_rules("score:*:100")
        assert rules[0].min_val is None
        assert rules[0].max_val == 100

    def test_wildcard_max(self):
        rules = parse_cap_rules("score:0:*")
        assert rules[0].min_val == 0
        assert rules[0].max_val is None

    def test_multiple_rules(self):
        rules = parse_cap_rules("a:0:10, b:*:50")
        assert len(rules) == 2

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid cap rule"):
            parse_cap_rules("bad_spec")


# ---------------------------------------------------------------------------
# cap_json_fields / cap_line
# ---------------------------------------------------------------------------
class TestCapLine:
    def test_caps_numeric_field(self):
        raw = _line(latency=999)
        rules = parse_cap_rules("latency:0:500")
        result = json.loads(cap_line(raw, rules))
        assert result["latency"] == 500

    def test_non_numeric_field_unchanged(self):
        raw = _line(level="info")
        rules = parse_cap_rules("level:0:100")
        result = json.loads(cap_line(raw, rules))
        assert result["level"] == "info"

    def test_plain_text_returned_unchanged(self):
        raw = "plain log line"
        rules = parse_cap_rules("x:0:10")
        assert cap_line(raw, rules) == raw

    def test_no_rules_returns_raw(self):
        raw = _line(x=200)
        assert cap_line(raw, []) == raw


# ---------------------------------------------------------------------------
# cap_output helpers
# ---------------------------------------------------------------------------
def test_make_cap_rules_none_returns_empty():
    assert make_cap_rules(None) == []


def test_make_cap_rules_returns_rules():
    rules = make_cap_rules("score:0:100")
    assert len(rules) == 1


def test_apply_capping_no_rules_unchanged():
    raw = _line(score=999)
    assert apply_capping(raw, []) == raw


def test_apply_capping_modifies_field():
    raw = _line(score=999)
    rules = make_cap_rules("score:0:100")
    result = json.loads(apply_capping(raw, rules))
    assert result["score"] == 100
