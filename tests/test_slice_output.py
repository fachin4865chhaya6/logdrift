import json
import pytest
from logdrift.slice_output import make_slice_rules, apply_slicing


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_slice_rules_none_returns_empty():
    assert make_slice_rules(None) == []


def test_make_slice_rules_empty_returns_empty():
    assert make_slice_rules("") == []


def test_make_slice_rules_returns_rules():
    rules = make_slice_rules("msg:0..4")
    assert len(rules) == 1
    assert rules[0].field == "msg"


def test_apply_slicing_no_rules_unchanged():
    raw = _line(msg="hello world")
    assert apply_slicing(raw, []) == raw


def test_apply_slicing_plain_text_unchanged():
    from logdrift.slicer import SliceRule
    rules = [SliceRule(field="msg", start=0, stop=3)]
    assert apply_slicing("plain text", rules) == "plain text"


def test_apply_slicing_modifies_field():
    from logdrift.slicer import SliceRule
    raw = _line(msg="hello world", level="info")
    rules = [SliceRule(field="msg", start=0, stop=5)]
    result = json.loads(apply_slicing(raw, rules))
    assert result["msg"] == "hello"
    assert result["level"] == "info"


def test_apply_slicing_multiple_rules():
    from logdrift.slicer import SliceRule
    raw = _line(msg="abcdef", tags=["x", "y", "z"])
    rules = [
        SliceRule(field="msg", start=0, stop=3),
        SliceRule(field="tags", start=1, stop=None),
    ]
    result = json.loads(apply_slicing(raw, rules))
    assert result["msg"] == "abc"
    assert result["tags"] == ["y", "z"]
