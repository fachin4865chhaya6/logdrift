"""Tests for logdrift.format_output."""
from __future__ import annotations

import json

from logdrift.format_output import make_format_rules, apply_formatting


def _line(**kw) -> str:
    return json.dumps(kw)


def test_make_format_rules_none_returns_empty():
    assert make_format_rules(None) == []


def test_make_format_rules_empty_returns_empty():
    assert make_format_rules("") == []


def test_make_format_rules_returns_rules():
    rules = make_format_rules("latency:{:.2f}")
    assert len(rules) == 1
    assert rules[0].field == "latency"


def test_apply_formatting_no_rules_unchanged():
    raw = _line(latency=1.23)
    assert apply_formatting(raw, []) == raw


def test_apply_formatting_formats_field():
    raw = _line(latency=3.14159)
    rules = make_format_rules("latency:{:.2f}")
    result = json.loads(apply_formatting(raw, rules))
    assert result["latency"] == "3.14"


def test_apply_formatting_plain_text_unchanged():
    rules = make_format_rules("latency:{:.2f}")
    assert apply_formatting("just text", rules) == "just text"


def test_apply_formatting_multiple_rules():
    raw = _line(latency=1.23456, score=99.9)
    rules = make_format_rules("latency:{:.1f},score:{:06.2f}")
    result = json.loads(apply_formatting(raw, rules))
    assert result["latency"] == "1.2"
    assert result["score"] == "099.90"
