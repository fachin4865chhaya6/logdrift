import json
import pytest
from logdrift.zipper import ZipRule, parse_zip_rules, zip_json_fields, zip_line


def _line(**kw) -> str:
    return json.dumps(kw)


class TestZipRule:
    def test_empty_sources_raises(self):
        with pytest.raises(ValueError):
            ZipRule(sources=[], dest="out")

    def test_empty_dest_raises(self):
        with pytest.raises(ValueError):
            ZipRule(sources=["a"], dest="")

    def test_apply_list(self):
        rule = ZipRule(sources=["a", "b"], dest="zipped")
        data = {"a": 1, "b": 2}
        result = rule.apply(data)
        assert result["zipped"] == [1, 2]

    def test_apply_dict(self):
        rule = ZipRule(sources=["x", "y"], dest="out", as_dict=True)
        data = {"x": "hello", "y": "world"}
        result = rule.apply(data)
        assert result["out"] == {"x": "hello", "y": "world"}

    def test_missing_source_value_is_none(self):
        rule = ZipRule(sources=["a", "missing"], dest="z")
        data = {"a": 10}
        result = rule.apply(data)
        assert result["z"] == [10, None]


class TestParseZipRules:
    def test_none_returns_empty(self):
        assert parse_zip_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_zip_rules("") == []

    def test_single_rule(self):
        rules = parse_zip_rules("a,b->out")
        assert len(rules) == 1
        assert rules[0].sources == ["a", "b"]
        assert rules[0].dest == "out"
        assert rules[0].as_dict is False

    def test_dict_flag(self):
        rules = parse_zip_rules("a,b->out:dict")
        assert rules[0].as_dict is True

    def test_multiple_rules(self):
        rules = parse_zip_rules("a,b->z1;c,d->z2")
        assert len(rules) == 2

    def test_missing_arrow_raises(self):
        with pytest.raises(ValueError):
            parse_zip_rules("a,b,dest")


class TestZipJsonFields:
    def test_plain_text_unchanged(self):
        assert zip_json_fields("hello world", [ZipRule(["a"], "z")]) == "hello world"

    def test_json_array_unchanged(self):
        raw = json.dumps([1, 2, 3])
        assert zip_json_fields(raw, [ZipRule(["a"], "z")]) == raw

    def test_no_rules_unchanged(self):
        raw = _line(a=1, b=2)
        assert zip_json_fields(raw, []) == raw

    def test_fields_zipped_into_list(self):
        raw = _line(a=1, b=2, c=3)
        rules = parse_zip_rules("a,b->pair")
        result = json.loads(zip_json_fields(raw, rules))
        assert result["pair"] == [1, 2]
        assert result["c"] == 3

    def test_fields_zipped_into_dict(self):
        raw = _line(x="foo", y="bar")
        rules = parse_zip_rules("x,y->combo:dict")
        result = json.loads(zip_json_fields(raw, rules))
        assert result["combo"] == {"x": "foo", "y": "bar"}

    def test_zip_line_delegates(self):
        raw = _line(a=5, b=6)
        rules = parse_zip_rules("a,b->nums")
        assert zip_line(raw, rules) == zip_json_fields(raw, rules)
