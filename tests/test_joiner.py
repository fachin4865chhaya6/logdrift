"""Tests for logdrift.joiner."""
from __future__ import annotations

import json
import pytest

from logdrift.joiner import (
    JoinRule,
    join_json_fields,
    join_line,
    parse_join_rules,
)


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# JoinRule construction
# ---------------------------------------------------------------------------

class TestJoinRule:
    def test_empty_sources_raises(self):
        with pytest.raises(ValueError, match="sources"):
            JoinRule(sources=[], dest="out")

    def test_empty_dest_raises(self):
        with pytest.raises(ValueError, match="dest"):
            JoinRule(sources=["a"], dest="")

    def test_whitespace_dest_raises(self):
        with pytest.raises(ValueError, match="dest"):
            JoinRule(sources=["a"], dest="   ")

    def test_apply_joins_two_fields(self):
        rule = JoinRule(sources=["first", "last"], dest="full")
        result = rule.apply({"first": "Ada", "last": "Lovelace"})
        assert result["full"] == "Ada Lovelace"

    def test_apply_custom_separator(self):
        rule = JoinRule(sources=["a", "b"], dest="c", sep="-")
        result = rule.apply({"a": "foo", "b": "bar"})
        assert result["c"] == "foo-bar"

    def test_apply_missing_source_skipped(self):
        rule = JoinRule(sources=["x", "y"], dest="z")
        result = rule.apply({"x": "hello"})
        assert result["z"] == "hello"

    def test_apply_no_matching_sources_no_dest_set(self):
        rule = JoinRule(sources=["x", "y"], dest="z")
        result = rule.apply({"a": "nope"})
        assert "z" not in result

    def test_apply_numeric_values_coerced_to_str(self):
        rule = JoinRule(sources=["code", "msg"], dest="full", sep=": ")
        result = rule.apply({"code": 404, "msg": "not found"})
        assert result["full"] == "404: not found"


# ---------------------------------------------------------------------------
# parse_join_rules
# ---------------------------------------------------------------------------

class TestParseJoinRules:
    def test_none_returns_empty(self):
        assert parse_join_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_join_rules("") == []

    def test_whitespace_returns_empty(self):
        assert parse_join_rules("   ") == []

    def test_single_rule(self):
        rules = parse_join_rules("full=first,last")
        assert len(rules) == 1
        assert rules[0].dest == "full"
        assert rules[0].sources == ["first", "last"]
        assert rules[0].sep == " "

    def test_custom_separator(self):
        rules = parse_join_rules("slug=a,b|-")
        assert rules[0].sep == "-"

    def test_multiple_rules(self):
        rules = parse_join_rules("full=first,last; path=dir,file|/")
        assert len(rules) == 2
        assert rules[1].sep == "/"

    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match="missing '='"):
            parse_join_rules("no_equals_here")


# ---------------------------------------------------------------------------
# join_line
# ---------------------------------------------------------------------------

class TestJoinLine:
    def test_plain_text_unchanged(self):
        rules = parse_join_rules("full=first,last")
        assert join_line("plain text", rules) == "plain text"

    def test_json_array_unchanged(self):
        rules = parse_join_rules("full=first,last")
        raw = json.dumps(["a", "b"])
        assert join_line(raw, rules) == raw

    def test_applies_rule(self):
        rules = parse_join_rules("full=first,last")
        raw = _line(first="Grace", last="Hopper")
        result = json.loads(join_line(raw, rules))
        assert result["full"] == "Grace Hopper"

    def test_no_rules_returns_raw(self):
        raw = _line(x=1)
        assert join_line(raw, []) == raw
