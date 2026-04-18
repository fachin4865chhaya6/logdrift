"""Tests for logdrift.flattener."""
import json
import pytest

from logdrift.flattener import (
    flatten_json,
    flatten_line,
    parse_flatten_depth,
)


class TestParseFlattenDepth:
    def test_none_returns_zero(self):
        assert parse_flatten_depth(None) == 0

    def test_valid_string_returns_int(self):
        assert parse_flatten_depth("3") == 3

    def test_zero_allowed(self):
        assert parse_flatten_depth("0") == 0

    def test_negative_raises(self):
        with pytest.raises(ValueError, match=">= 0"):
            parse_flatten_depth("-1")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid flatten depth"):
            parse_flatten_depth("deep")


class TestFlattenJson:
    def test_flat_dict_unchanged(self):
        data = {"a": 1, "b": 2}
        assert flatten_json(data) == {"a": 1, "b": 2}

    def test_nested_dict_flattened(self):
        data = {"a": {"b": {"c": 42}}}
        assert flatten_json(data) == {"a.b.c": 42}

    def test_mixed_nested(self):
        data = {"level": "info", "ctx": {"user": "alice", "req": {"id": 9}}}
        result = flatten_json(data)
        assert result["level"] == "info"
        assert result["ctx.user"] == "alice"
        assert result["ctx.req.id"] == 9

    def test_max_depth_limits_flattening(self):
        data = {"a": {"b": {"c": 1}}}
        result = flatten_json(data, max_depth=1)
        assert "a.b" not in result
        assert result["a"] == {"b": {"c": 1}}

    def test_max_depth_two(self):
        data = {"a": {"b": {"c": 1}}}
        result = flatten_json(data, max_depth=2)
        assert result["a.b"] == {"c": 1}

    def test_list_value_kept_as_is(self):
        data = {"tags": ["x", "y"]}
        assert flatten_json(data) == {"tags": ["x", "y"]}

    def test_empty_dict(self):
        assert flatten_json({}) == {}


class TestFlattenLine:
    def test_plain_text_returned_unchanged(self):
        assert flatten_line("not json") == "not json"

    def test_json_line_flattened(self):
        raw = json.dumps({"a": {"b": 1}})
        result = json.loads(flatten_line(raw))
        assert result == {"a.b": 1}

    def test_json_line_with_max_depth(self):
        raw = json.dumps({"a": {"b": {"c": 3}}})
        result = json.loads(flatten_line(raw, max_depth=1))
        assert result["a"] == {"b": {"c": 3}}

    def test_empty_json_object(self):
        raw = json.dumps({})
        result = json.loads(flatten_line(raw))
        assert result == {}
