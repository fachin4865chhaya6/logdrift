"""Tests for logdrift.cast_output."""
import json
from logdrift.cast_output import make_cast_rules, apply_casting


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_cast_rules_none_returns_empty():
    assert make_cast_rules(None) == []


def test_make_cast_rules_empty_returns_empty():
    assert make_cast_rules("") == []


def test_make_cast_rules_returns_rules():
    rules = make_cast_rules("count:int")
    assert len(rules) == 1
    assert rules[0].field == "count"


def test_apply_casting_no_rules_unchanged():
    line = _line(x="1")
    assert apply_casting(line, []) == line


def test_apply_casting_casts_field():
    rules = make_cast_rules("score:float")
    line = _line(score="2.5", level="info")
    result = json.loads(apply_casting(line, rules))
    assert result["score"] == pytest.approx(2.5)


def test_apply_casting_plain_text_unchanged():
    rules = make_cast_rules("x:int")
    assert apply_casting("not json", rules) == "not json"


import pytest
