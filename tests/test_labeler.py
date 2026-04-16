"""Tests for logdrift.labeler."""

import json
import pytest

from logdrift.labeler import parse_label_rules, label_line, inject_labels, LabelRule


class TestParseLabelRules:
    def test_none_returns_empty(self):
        assert parse_label_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_label_rules("") == []

    def test_single_path_rule(self):
        rules = parse_label_rules("error:path=level")
        assert len(rules) == 1
        assert rules[0].label == "error"
        assert rules[0].json_path == "level"

    def test_single_pattern_rule(self):
        rules = parse_label_rules("warn:pattern=WARN")
        assert len(rules) == 1
        assert rules[0].label == "warn"
        assert rules[0].pattern == "WARN"

    def test_threshold_rule(self):
        rules = parse_label_rules("slow:threshold=duration>500")
        assert len(rules) == 1
        assert rules[0].label == "slow"
        assert rules[0].json_path == "duration"
        assert rules[0].threshold == 500.0

    def test_multiple_rules(self):
        rules = parse_label_rules("err:path=error, warn:pattern=WARN")
        assert len(rules) == 2

    def test_invalid_rule_raises(self):
        with pytest.raises(ValueError):
            parse_label_rules("badrule")

    def test_empty_label_raises(self):
        with pytest.raises(ValueError):
            LabelRule(label="")


class TestLabelLine:
    def _json(self, **kw) -> str:
        return json.dumps(kw)

    def test_no_rules_returns_empty(self):
        assert label_line(self._json(level="error"), []) == []

    def test_path_rule_matches(self):
        rules = parse_label_rules("has_level:path=level")
        result = label_line(self._json(level="error"), rules)
        assert "has_level" in result

    def test_path_rule_no_match(self):
        rules = parse_label_rules("has_foo:path=foo")
        result = label_line(self._json(level="error"), rules)
        assert result == []

    def test_pattern_rule_matches(self):
        rules = parse_label_rules("warn:pattern=WARN")
        result = label_line("2024-01-01 WARN something happened", rules)
        assert "warn" in result

    def test_pattern_rule_no_match(self):
        rules = parse_label_rules("warn:pattern=WARN")
        result = label_line("INFO all good", rules)
        assert result == []

    def test_threshold_rule_matches(self):
        rules = parse_label_rules("slow:threshold=duration>100")
        result = label_line(self._json(duration=250), rules)
        assert "slow" in result

    def test_threshold_rule_not_exceeded(self):
        rules = parse_label_rules("slow:threshold=duration>100")
        result = label_line(self._json(duration=50), rules)
        assert result == []

    def test_threshold_non_numeric_skipped(self):
        rules = parse_label_rules("slow:threshold=duration>100")
        result = label_line(self._json(duration="fast"), rules)
        assert result == []

    def test_plain_text_path_rule_no_match(self):
        rules = parse_label_rules("has_level:path=level")
        result = label_line("plain text line", rules)
        assert result == []


class TestInjectLabels:
    def test_no_labels_returns_original(self):
        raw = json.dumps({"msg": "hi"})
        assert inject_labels(raw, []) == raw

    def test_labels_injected(self):
        raw = json.dumps({"msg": "hi"})
        result = inject_labels(raw, ["error", "slow"])
        data = json.loads(result)
        assert data["_labels"] == ["error", "slow"]

    def test_plain_text_returned_unchanged(self):
        raw = "plain log line"
        assert inject_labels(raw, ["warn"]) == raw
