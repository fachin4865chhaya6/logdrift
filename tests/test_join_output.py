"""Tests for logdrift.join_output."""
from __future__ import annotations

import json

from logdrift.join_output import apply_joining, make_join_rules


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_join_rules_none_returns_empty():
    assert make_join_rules(None) == []


def test_make_join_rules_empty_returns_empty():
    assert make_join_rules("") == []


def test_make_join_rules_returns_rules():
    rules = make_join_rules("out=a,b")
    assert len(rules) == 1
    assert rules[0].dest == "out"


def test_apply_joining_no_rules_unchanged():
    raw = _line(a="x", b="y")
    assert apply_joining(raw, []) == raw


def test_apply_joining_transforms_line():
    rules = make_join_rules("full=first,last| ")
    raw = _line(first="Linus", last="Torvalds")
    result = json.loads(apply_joining(raw, rules))
    assert result["full"] == "Linus Torvalds"


def test_apply_joining_plain_text_unchanged():
    rules = make_join_rules("full=first,last")
    assert apply_joining("not json", rules) == "not json"
