import json
import pytest
from logdrift.padder import PadRule, parse_pad_rules, pad_json_fields, pad_line


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestPadRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            PadRule(field="", width=10)

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError, match="field"):
            PadRule(field="   ", width=10)

    def test_zero_width_raises(self):
        with pytest.raises(ValueError, match="width"):
            PadRule(field="x", width=0)

    def test_negative_width_raises(self):
        with pytest.raises(ValueError, match="width"):
            PadRule(field="x", width=-5)

    def test_invalid_align_raises(self):
        with pytest.raises(ValueError, match="align"):
            PadRule(field="x", width=10, align="middle")

    def test_multi_char_fill_raises(self):
        with pytest.raises(ValueError, match="fill_char"):
            PadRule(field="x", width=10, fill_char="--")

    def test_apply_left_pad(self):
        rule = PadRule(field="msg", width=10, align="left")
        assert rule.apply("hi") == "hi        "

    def test_apply_right_pad(self):
        rule = PadRule(field="code", width=6, align="right", fill_char="0")
        assert rule.apply("42") == "000042"

    def test_apply_center_pad(self):
        rule = PadRule(field="label", width=9, align="center")
        result = rule.apply("abc")
        assert result == "   abc   "

    def test_apply_converts_non_string(self):
        rule = PadRule(field="n", width=8, align="right")
        assert rule.apply(123) == "     123"

    def test_apply_value_longer_than_width(self):
        rule = PadRule(field="x", width=3, align="left")
        assert rule.apply("toolong") == "toolong"


class TestParsePadRules:
    def test_none_returns_empty(self):
        assert parse_pad_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_pad_rules("") == []

    def test_whitespace_returns_empty(self):
        assert parse_pad_rules("   ") == []

    def test_single_rule_defaults(self):
        rules = parse_pad_rules("status:10")
        assert len(rules) == 1
        assert rules[0].field == "status"
        assert rules[0].width == 10
        assert rules[0].align == "left"
        assert rules[0].fill_char == " "

    def test_single_rule_with_align(self):
        rules = parse_pad_rules("code:8:right")
        assert rules[0].align == "right"

    def test_single_rule_with_fill_char(self):
        rules = parse_pad_rules("id:6:right:0")
        assert rules[0].fill_char == "0"

    def test_multiple_rules(self):
        rules = parse_pad_rules("a:5,b:10:center")
        assert len(rules) == 2
        assert rules[0].field == "a"
        assert rules[1].field == "b"

    def test_invalid_width_raises(self):
        with pytest.raises(ValueError, match="width"):
            parse_pad_rules("x:notanumber")

    def test_missing_width_raises(self):
        with pytest.raises(ValueError):
            parse_pad_rules("x")


class TestPadLine:
    def test_plain_text_unchanged(self):
        rules = parse_pad_rules("msg:10")
        assert pad_line("hello world", rules) == "hello world"

    def test_json_array_unchanged(self):
        rules = parse_pad_rules("msg:10")
        raw = json.dumps([1, 2, 3])
        assert pad_line(raw, rules) == raw

    def test_no_rules_returns_raw(self):
        raw = _line(msg="hi")
        assert pad_line(raw, []) == raw

    def test_pads_matching_field(self):
        raw = _line(status="ok")
        rules = parse_pad_rules("status:10:left")
        result = json.loads(pad_line(raw, rules))
        assert result["status"] == "ok        "

    def test_unrelated_field_unchanged(self):
        raw = _line(status="ok", level="info")
        rules = parse_pad_rules("status:10")
        result = json.loads(pad_line(raw, rules))
        assert result["level"] == "info"

    def test_missing_field_skipped(self):
        raw = _line(level="info")
        rules = parse_pad_rules("missing:10")
        result = json.loads(pad_line(raw, rules))
        assert result == {"level": "info"}
