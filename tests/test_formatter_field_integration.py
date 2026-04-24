"""Integration tests: format_output wired through a simulated pipeline."""
from __future__ import annotations

import json

from logdrift.format_output import make_format_rules, apply_formatting


def _line(**kw) -> str:
    return json.dumps(kw)


def test_pipeline_formats_all_matching_lines():
    lines = [
        _line(latency=0.1234, user="alice"),
        _line(latency=9.9999, user="bob"),
        "plain text line",
    ]
    rules = make_format_rules("latency:{:.2f}")
    results = [apply_formatting(ln, rules) for ln in lines]

    assert json.loads(results[0])["latency"] == "0.12"
    assert json.loads(results[1])["latency"] == "10.00"
    assert results[2] == "plain text line"


def test_pipeline_preserves_unrelated_fields():
    raw = _line(latency=1.5, status=200, user="carol")
    rules = make_format_rules("latency:{:.0f}")
    result = json.loads(apply_formatting(raw, rules))
    assert result["status"] == 200
    assert result["user"] == "carol"


def test_pipeline_chained_rules_applied_in_order():
    raw = _line(latency=3.14159, score=42.0)
    rules = make_format_rules("latency:{:.1f},score:{:+.0f}")
    result = json.loads(apply_formatting(raw, rules))
    assert result["latency"] == "3.1"
    assert result["score"] == "+42"


def test_pipeline_no_rules_is_identity():
    raw = _line(latency=1.0, user="dave")
    rules = make_format_rules(None)
    assert apply_formatting(raw, rules) == raw
