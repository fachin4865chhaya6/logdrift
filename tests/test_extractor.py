"""Tests for logdrift.extractor."""
import json
import pytest
from logdrift.extractor import (
    ExtractRule,
    parse_extract_rules,
    extract_json_fields,
    extract_line,
)


def _line(data: dict) -> str:
    return json.dumps(data)


class TestExtractRule:
    def test_empty_source_raises(self):
        with pytest.raises(ValueError):
            ExtractRule(source="", dest="dst")

    def test_empty_dest_raises(self):
        with pytest.raises(ValueError):
            ExtractRule(source="a.b", dest="")

    def test_resolve_top_level(self):
        rule = ExtractRule(source="level", dest="lvl")
        assert rule.resolve({"level": "info"}) == "info"

    def test_resolve_nested(self):
        rule = ExtractRule(source="meta.method", dest="method")
        assert rule.resolve({"meta": {"method": "GET"}}) == "GET"

    def test_resolve_missing_returns_none(self):
        rule = ExtractRule(source="meta.missing", dest="x")
        assert rule.resolve({"meta": {}}) is None

    def test_resolve_non_dict_intermediate_returns_none(self):
        rule = ExtractRule(source="a.b.c", dest="x")
        assert rule.resolve({"a": "not-a-dict"}) is None


class TestParseExtractRules:
    def test_none_returns_empty(self):
        assert parse_extract_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_extract_rules("") == []

    def test_single_rule(self):
        rules = parse_extract_rules("meta.method:method")
        assert len(rules) == 1
        assert rules[0].source == "meta.method"
        assert rules[0].dest == "method"

    def test_multiple_rules(self):
        rules = parse_extract_rules("a.b:x,c.d:y")
        assert len(rules) == 2

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError):
            parse_extract_rules("nodest")

    def test_whitespace_stripped(self):
        rules = parse_extract_rules(" a.b : x ")
        assert rules[0].source == "a.b"
        assert rules[0].dest == "x"


class TestExtractJsonFields:
    def test_injects_value(self):
        rules = parse_extract_rules("meta.method:method")
        result = extract_json_fields({"meta": {"method": "POST"}}, rules)
        assert result["method"] == "POST"

    def test_original_keys_preserved(self):
        rules = parse_extract_rules("a:b")
        result = extract_json_fields({"a": 1, "other": 2}, rules)
        assert result["other"] == 2

    def test_missing_path_not_injected(self):
        rules = parse_extract_rules("x.y:z")
        result = extract_json_fields({"a": 1}, rules)
        assert "z" not in result


class TestExtractLine:
    def test_plain_text_unchanged(self):
        assert extract_line("hello world", parse_extract_rules("a:b")) == "hello world"

    def test_json_array_unchanged(self):
        line = json.dumps([1, 2])
        assert extract_line(line, parse_extract_rules("a:b")) == line

    def test_no_rules_returns_original(self):
        line = _line({"a": 1})
        assert extract_line(line, []) == line

    def test_extracts_nested_field(self):
        line = _line({"req": {"status": 200}})
        result = json.loads(extract_line(line, parse_extract_rules("req.status:status")))
        assert result["status"] == 200

    def test_multiple_rules_applied(self):
        line = _line({"a": {"x": 1}, "b": {"y": 2}})
        rules = parse_extract_rules("a.x:ax,b.y:by")
        result = json.loads(extract_line(line, rules))
        assert result["ax"] == 1
        assert result["by"] == 2
