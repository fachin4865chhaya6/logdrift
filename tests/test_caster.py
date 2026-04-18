"""Tests for logdrift.caster."""
import json
import pytest
from logdrift.caster import CastRule, parse_cast_rules, cast_json_fields, cast_line


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestCastRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            CastRule(field="", cast_type="int")

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError):
            CastRule(field="x", cast_type="list")

    def test_apply_int(self):
        assert CastRule("x", "int").apply("42") == 42

    def test_apply_float(self):
        assert CastRule("x", "float").apply("3.14") == pytest.approx(3.14)

    def test_apply_bool_false_string(self):
        assert CastRule("x", "bool").apply("false") is False

    def test_apply_bool_true_string(self):
        assert CastRule("x", "bool").apply("yes") is True

    def test_apply_bool_already_bool(self):
        assert CastRule("x", "bool").apply(True) is True

    def test_apply_str(self):
        assert CastRule("x", "str").apply(99) == "99"


class TestParseCastRules:
    def test_none_returns_empty(self):
        assert parse_cast_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_cast_rules("") == []

    def test_single_rule(self):
        rules = parse_cast_rules("count:int")
        assert len(rules) == 1
        assert rules[0].field == "count"
        assert rules[0].cast_type == "int"

    def test_multiple_rules(self):
        rules = parse_cast_rules("count:int,ratio:float")
        assert len(rules) == 2

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError):
            parse_cast_rules("badspec")

    def test_strips_whitespace(self):
        rules = parse_cast_rules(" score : float ")
        assert rules[0].field == "score"
        assert rules[0].cast_type == "float"


class TestCastJsonFields:
    def test_casts_matching_field(self):
        rules = parse_cast_rules("count:int")
        result = cast_json_fields({"count": "7", "msg": "hi"}, rules)
        assert result["count"] == 7
        assert result["msg"] == "hi"

    def test_missing_field_ignored(self):
        rules = parse_cast_rules("missing:int")
        data = {"other": "1"}
        assert cast_json_fields(data, rules) == data

    def test_bad_cast_leaves_value(self):
        rules = parse_cast_rules("x:int")
        result = cast_json_fields({"x": "notanint"}, rules)
        assert result["x"] == "notanint"


class TestCastLine:
    def test_plain_text_unchanged(self):
        rules = parse_cast_rules("x:int")
        assert cast_line("plain text", rules) == "plain text"

    def test_json_array_unchanged(self):
        rules = parse_cast_rules("x:int")
        line = json.dumps([1, 2])
        assert cast_line(line, rules) == line

    def test_casts_json_field(self):
        rules = parse_cast_rules("n:int")
        line = _line(n="5", msg="ok")
        result = json.loads(cast_line(line, rules))
        assert result["n"] == 5

    def test_no_rules_returns_unchanged(self):
        line = _line(n="5")
        assert cast_line(line, []) == line
