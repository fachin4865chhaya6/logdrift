"""Tests for logdrift.extract_output."""
import json
from logdrift.extract_output import make_extract_rules, apply_extraction


def _line(data: dict) -> str:
    return json.dumps(data)


def test_make_extract_rules_none_returns_empty():
    assert make_extract_rules(None) == []


def test_make_extract_rules_empty_returns_empty():
    assert make_extract_rules("") == []


def test_make_extract_rules_returns_rules():
    rules = make_extract_rules("a.b:x")
    assert len(rules) == 1


def test_apply_extraction_no_rules_unchanged():
    line = _line({"a": 1})
    assert apply_extraction(line, []) == line


def test_apply_extraction_injects_field():
    line = _line({"meta": {"env": "prod"}})
    rules = make_extract_rules("meta.env:env")
    result = json.loads(apply_extraction(line, rules))
    assert result["env"] == "prod"


def test_apply_extraction_plain_text_unchanged():
    rules = make_extract_rules("a.b:x")
    assert apply_extraction("not json", rules) == "not json"
