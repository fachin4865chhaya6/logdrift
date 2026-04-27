"""Tests for logdrift.stringer and logdrift.string_output."""
from __future__ import annotations

import json
import pytest

from logdrift.stringer import (
    StringRule,
    apply_string_ops,
    parse_string_rules,
    string_line,
)
from logdrift.string_output import apply_string_ops_to_line, make_string_rules


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# StringRule construction
# ---------------------------------------------------------------------------

class TestStringRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field must not be empty"):
            StringRule(field="", op="strip")

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError, match="field must not be empty"):
            StringRule(field="  ", op="upper")

    def test_unsupported_op_raises(self):
        with pytest.raises(ValueError, match="unsupported op"):
            StringRule(field="msg", op="explode")

    def test_replace_missing_colon_raises(self):
        with pytest.raises(ValueError, match="replace arg must be"):
            StringRule(field="msg", op="replace", arg="nocolon")

    def test_apply_strip(self):
        r = StringRule(field="msg", op="strip")
        assert r.apply("  hello  ") == "hello"

    def test_apply_lstrip(self):
        r = StringRule(field="msg", op="lstrip")
        assert r.apply("  hi") == "hi"

    def test_apply_rstrip(self):
        r = StringRule(field="msg", op="rstrip")
        assert r.apply("hi  ") == "hi"

    def test_apply_upper(self):
        r = StringRule(field="msg", op="upper")
        assert r.apply("hello") == "HELLO"

    def test_apply_lower(self):
        r = StringRule(field="msg", op="lower")
        assert r.apply("HELLO") == "hello"

    def test_apply_title(self):
        r = StringRule(field="msg", op="title")
        assert r.apply("hello world") == "Hello World"

    def test_apply_replace(self):
        r = StringRule(field="msg", op="replace", arg="foo:bar")
        assert r.apply("foo baz foo") == "bar baz bar"

    def test_apply_prefix(self):
        r = StringRule(field="msg", op="prefix", arg="[INFO] ")
        assert r.apply("started") == "[INFO] started"

    def test_apply_suffix(self):
        r = StringRule(field="msg", op="suffix", arg="!")
        assert r.apply("done") == "done!"

    def test_apply_non_string_value_unchanged(self):
        r = StringRule(field="count", op="upper")
        assert r.apply(42) == 42


# ---------------------------------------------------------------------------
# parse_string_rules
# ---------------------------------------------------------------------------

def test_none_returns_empty():
    assert parse_string_rules(None) == []

def test_empty_string_returns_empty():
    assert parse_string_rules("") == []

def test_single_rule():
    rules = parse_string_rules("msg:upper")
    assert len(rules) == 1
    assert rules[0].field == "msg"
    assert rules[0].op == "upper"

def test_multiple_rules():
    rules = parse_string_rules("msg:strip,level:lower")
    assert len(rules) == 2

def test_rule_with_arg():
    rules = parse_string_rules("msg:replace:err:ERROR")
    assert rules[0].arg == "err:ERROR"

def test_invalid_token_raises():
    with pytest.raises(ValueError, match="invalid string rule token"):
        parse_string_rules("justfield")


# ---------------------------------------------------------------------------
# apply_string_ops / string_line
# ---------------------------------------------------------------------------

def test_apply_string_ops_modifies_matching_field():
    rules = [StringRule(field="msg", op="upper")]
    result = apply_string_ops({"msg": "hello", "level": "info"}, rules)
    assert result["msg"] == "HELLO"
    assert result["level"] == "info"

def test_apply_string_ops_skips_missing_field():
    rules = [StringRule(field="missing", op="upper")]
    data = {"msg": "hello"}
    assert apply_string_ops(data, rules) == data

def test_string_line_plain_text_unchanged():
    rules = [StringRule(field="msg", op="upper")]
    assert string_line("plain text", rules) == "plain text"

def test_string_line_no_rules_unchanged():
    raw = _line(msg="hello")
    assert string_line(raw, []) == raw

def test_string_line_transforms_field():
    raw = _line(msg="  hello  ")
    rules = [StringRule(field="msg", op="strip")]
    result = json.loads(string_line(raw, rules))
    assert result["msg"] == "hello"


# ---------------------------------------------------------------------------
# string_output helpers
# ---------------------------------------------------------------------------

def test_make_string_rules_none_returns_empty():
    assert make_string_rules(None) == []

def test_make_string_rules_returns_rules():
    rules = make_string_rules("msg:lower")
    assert len(rules) == 1

def test_apply_string_ops_to_line_no_rules_unchanged():
    raw = _line(msg="Hello")
    assert apply_string_ops_to_line(raw, []) == raw

def test_apply_string_ops_to_line_applies_rule():
    raw = _line(msg="Hello World")
    rules = make_string_rules("msg:lower")
    result = json.loads(apply_string_ops_to_line(raw, rules))
    assert result["msg"] == "hello world"
