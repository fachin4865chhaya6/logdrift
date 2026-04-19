import json
import pytest
from logdrift.slicer import SliceRule, parse_slice_rules, slice_json_fields, slice_line


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestSliceRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            SliceRule(field="", start=0, stop=3)

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            SliceRule(field="  ", start=0, stop=3)

    def test_no_start_or_stop_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            SliceRule(field="msg", start=None, stop=None)

    def test_apply_string_with_start_and_stop(self):
        rule = SliceRule(field="msg", start=0, stop=5)
        assert rule.apply("hello world") == "hello"

    def test_apply_string_with_start_only(self):
        rule = SliceRule(field="msg", start=6, stop=None)
        assert rule.apply("hello world") == "world"

    def test_apply_string_with_stop_only(self):
        rule = SliceRule(field="msg", start=None, stop=3)
        assert rule.apply("abcdef") == "abc"

    def test_apply_list(self):
        rule = SliceRule(field="tags", start=1, stop=3)
        assert rule.apply(["a", "b", "c", "d"]) == ["b", "c"]

    def test_apply_non_sliceable_returns_unchanged(self):
        rule = SliceRule(field="count", start=0, stop=2)
        assert rule.apply(42) == 42


class TestParseSliceRules:
    def test_none_returns_empty(self):
        assert parse_slice_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_slice_rules("") == []

    def test_single_rule_start_stop(self):
        rules = parse_slice_rules("msg:0..5")
        assert len(rules) == 1
        assert rules[0].field == "msg"
        assert rules[0].start == 0
        assert rules[0].stop == 5

    def test_single_rule_start_only(self):
        rules = parse_slice_rules("msg:2..")
        assert rules[0].start == 2
        assert rules[0].stop is None

    def test_single_rule_stop_only(self):
        rules = parse_slice_rules("msg:..4")
        assert rules[0].start is None
        assert rules[0].stop == 4

    def test_multiple_rules(self):
        rules = parse_slice_rules("msg:0..3, tags:1..2")
        assert len(rules) == 2
        assert rules[1].field == "tags"

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="missing ':'"):
            parse_slice_rules("msgonly")

    def test_empty_field_in_spec_raises(self):
        with pytest.raises(ValueError, match="empty field"):
            parse_slice_rules(":0..3")


class TestSliceJsonFields:
    def test_applies_rule_to_matching_field(self):
        data = {"msg": "hello world", "level": "info"}
        rules = [SliceRule(field="msg", start=0, stop=5)]
        result = slice_json_fields(data, rules)
        assert result["msg"] == "hello"
        assert result["level"] == "info"

    def test_missing_field_unchanged(self):
        data = {"level": "info"}
        rules = [SliceRule(field="msg", start=0, stop=3)]
        result = slice_json_fields(data, rules)
        assert result == {"level": "info"}

    def test_does_not_mutate_original(self):
        data = {"msg": "hello"}
        rules = [SliceRule(field="msg", start=0, stop=3)]
        slice_json_fields(data, rules)
        assert data["msg"] == "hello"


class TestSliceLine:
    def test_plain_text_returned_unchanged(self):
        assert slice_line("not json", [SliceRule(field="msg", start=0, stop=3)]) == "not json"

    def test_json_array_returned_unchanged(self):
        raw = json.dumps([1, 2, 3])
        assert slice_line(raw, [SliceRule(field="x", start=0, stop=1)]) == raw

    def test_no_rules_returns_raw(self):
        raw = _line(msg="hello")
        assert slice_line(raw, []) == raw

    def test_slices_field_in_json(self):
        raw = _line(msg="hello world")
        rules = [SliceRule(field="msg", start=0, stop=5)]
        result = json.loads(slice_line(raw, rules))
        assert result["msg"] == "hello"
