import pytest
from logdrift.validator import (
    ValidationRule,
    parse_validation_rules,
    validate_line,
)
import json


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestValidationRule:
    def test_empty_path_raises(self):
        with pytest.raises(ValueError):
            ValidationRule(json_path="", pattern="\\d+")

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError):
            ValidationRule(json_path="level", pattern="")

    def test_validate_matching_value_returns_true(self):
        rule = ValidationRule(json_path="level", pattern="^(INFO|WARN|ERROR)$")
        data = {"level": "INFO", "msg": "ok"}
        assert rule.validate(data) is True

    def test_validate_non_matching_value_returns_false(self):
        rule = ValidationRule(json_path="level", pattern="^(INFO|WARN|ERROR)$")
        data = {"level": "DEBUG", "msg": "ok"}
        assert rule.validate(data) is False

    def test_validate_missing_field_returns_false(self):
        rule = ValidationRule(json_path="level", pattern="INFO")
        assert rule.validate({"msg": "hello"}) is False

    def test_default_tag_is_invalid(self):
        rule = ValidationRule(json_path="level", pattern="INFO")
        assert rule.tag == "invalid"

    def test_custom_tag_stored(self):
        rule = ValidationRule(json_path="level", pattern="INFO", tag="bad-level")
        assert rule.tag == "bad-level"


class TestParseValidationRules:
    def test_none_returns_empty(self):
        assert parse_validation_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_validation_rules("") == []

    def test_single_rule_two_segments(self):
        rules = parse_validation_rules("level:INFO")
        assert len(rules) == 1
        assert rules[0].json_path == "level"
        assert rules[0].pattern == "INFO"
        assert rules[0].tag == "invalid"

    def test_single_rule_with_tag(self):
        rules = parse_validation_rules("level:INFO:bad-level")
        assert rules[0].tag == "bad-level"

    def test_multiple_rules(self):
        rules = parse_validation_rules("level:INFO,status:\\d+:bad-status")
        assert len(rules) == 2

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError):
            parse_validation_rules("onlyone")


class TestValidateLine:
    def test_no_rules_returns_empty_failed(self):
        raw = _line(level="INFO")
        _, failed = validate_line(raw, [])
        assert failed == []

    def test_plain_text_returns_empty_failed(self):
        from logdrift.validator import ValidationRule
        rules = [ValidationRule(json_path="level", pattern="INFO")]
        _, failed = validate_line("not json", rules)
        assert failed == []

    def test_all_pass_returns_empty_failed(self):
        rules = [ValidationRule(json_path="level", pattern="INFO")]
        _, failed = validate_line(_line(level="INFO"), rules)
        assert failed == []

    def test_one_fail_returns_tag(self):
        rules = [ValidationRule(json_path="level", pattern="INFO", tag="bad-level")]
        _, failed = validate_line(_line(level="DEBUG"), rules)
        assert failed == ["bad-level"]

    def test_multiple_failures_all_reported(self):
        rules = [
            ValidationRule(json_path="level", pattern="INFO", tag="t1"),
            ValidationRule(json_path="status", pattern="^2\\d{2}$", tag="t2"),
        ]
        _, failed = validate_line(_line(level="ERROR", status="500"), rules)
        assert set(failed) == {"t1", "t2"}
