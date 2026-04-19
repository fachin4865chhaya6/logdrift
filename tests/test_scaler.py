import json
import pytest
from logdrift.scaler import ScaleRule, parse_scale_rules, scale_json_fields, scale_line


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestScaleRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="empty"):
            ScaleRule(field="", factor=2.0)

    def test_zero_factor_raises(self):
        with pytest.raises(ValueError, match="zero"):
            ScaleRule(field="latency", factor=0)

    def test_apply_factor_only(self):
        rule = ScaleRule(field="latency", factor=1000.0)
        assert rule.apply(0.5) == pytest.approx(500.0)

    def test_apply_factor_and_offset(self):
        rule = ScaleRule(field="temp", factor=1.8, offset=32.0)
        assert rule.apply(100.0) == pytest.approx(212.0)

    def test_negative_factor(self):
        rule = ScaleRule(field="x", factor=-1.0)
        assert rule.apply(5.0) == pytest.approx(-5.0)


class TestParseScaleRules:
    def test_none_returns_empty(self):
        assert parse_scale_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_scale_rules("") == []

    def test_whitespace_returns_empty(self):
        assert parse_scale_rules("   ") == []

    def test_single_rule_no_offset(self):
        rules = parse_scale_rules("latency:1000")
        assert len(rules) == 1
        assert rules[0].field == "latency"
        assert rules[0].factor == pytest.approx(1000.0)
        assert rules[0].offset == pytest.approx(0.0)

    def test_single_rule_with_offset(self):
        rules = parse_scale_rules("temp:1.8:32")
        assert len(rules) == 1
        assert rules[0].factor == pytest.approx(1.8)
        assert rules[0].offset == pytest.approx(32.0)

    def test_multiple_rules(self):
        rules = parse_scale_rules("a:2,b:0.5:10")
        assert len(rules) == 2
        assert rules[0].field == "a"
        assert rules[1].field == "b"

    def test_missing_factor_raises(self):
        with pytest.raises(ValueError):
            parse_scale_rules("latency")

    def test_invalid_factor_raises(self):
        with pytest.raises(ValueError):
            parse_scale_rules("latency:abc")

    def test_invalid_offset_raises(self):
        with pytest.raises(ValueError):
            parse_scale_rules("latency:2:abc")


class TestScaleJsonFields:
    def test_scales_numeric_field(self):
        rules = [ScaleRule(field="ms", factor=0.001)]
        result = scale_json_fields({"ms": 500}, rules)
        assert result["ms"] == pytest.approx(0.5)

    def test_missing_field_unchanged(self):
        rules = [ScaleRule(field="missing", factor=2.0)]
        result = scale_json_fields({"other": 1}, rules)
        assert result == {"other": 1}

    def test_non_numeric_field_unchanged(self):
        rules = [ScaleRule(field="name", factor=2.0)]
        result = scale_json_fields({"name": "alice"}, rules)
        assert result["name"] == "alice"

    def test_does_not_mutate_original(self):
        data = {"x": 10}
        rules = [ScaleRule(field="x", factor=3.0)]
        scale_json_fields(data, rules)
        assert data["x"] == 10


class TestScaleLine:
    def test_scales_field_in_json_line(self):
        raw = _line(latency=200)
        rules = [ScaleRule(field="latency", factor=0.001)]
        result = json.loads(scale_line(raw, rules))
        assert result["latency"] == pytest.approx(0.2)

    def test_plain_text_unchanged(self):
        rules = [ScaleRule(field="x", factor=2.0)]
        assert scale_line("not json", rules) == "not json"

    def test_no_rules_returns_raw(self):
        raw = _line(x=5)
        assert scale_line(raw, []) == raw

    def test_json_array_unchanged(self):
        raw = json.dumps([1, 2, 3])
        rules = [ScaleRule(field="x", factor=2.0)]
        assert scale_line(raw, rules) == raw
