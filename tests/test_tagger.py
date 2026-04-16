"""Tests for logdrift.tagger."""

import json
import pytest

from logdrift.tagger import parse_tag_rules, tag_line, inject_tags


# ---------------------------------------------------------------------------
# parse_tag_rules
# ---------------------------------------------------------------------------

class TestParseTagRules:
    def test_none_returns_empty(self):
        assert parse_tag_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_tag_rules("") == []

    def test_single_rule(self):
        rules = parse_tag_rules("error:ERROR")
        assert rules == [{"tag": "error", "pattern": "ERROR"}]

    def test_multiple_rules(self):
        rules = parse_tag_rules("error:ERROR,warn:WARN")
        assert len(rules) == 2
        assert rules[0]["tag"] == "error"
        assert rules[1]["tag"] == "warn"

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="Invalid tag rule"):
            parse_tag_rules("badformat")

    def test_empty_tag_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_tag_rules(":pattern")

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_tag_rules("tag:")

    def test_whitespace_stripped(self):
        rules = parse_tag_rules(" error : ERROR ")
        assert rules == [{"tag": "error", "pattern": "ERROR"}]


# ---------------------------------------------------------------------------
# tag_line
# ---------------------------------------------------------------------------

class TestTagLine:
    def test_no_rules_returns_empty(self):
        assert tag_line("some log line", []) == []

    def test_plain_text_match(self):
        rules = parse_tag_rules("error:ERROR")
        assert tag_line("ERROR something happened", rules) == ["error"]

    def test_plain_text_no_match(self):
        rules = parse_tag_rules("error:ERROR")
        assert tag_line("everything is fine", rules) == []

    def test_multiple_tags_returned(self):
        rules = parse_tag_rules("error:ERROR,critical:CRITICAL")
        line = "ERROR CRITICAL meltdown"
        tags = tag_line(line, rules)
        assert "error" in tags
        assert "critical" in tags

    def test_json_field_match(self):
        rules = parse_tag_rules("error:ERROR")
        line = json.dumps({"level": "ERROR", "msg": "boom"})
        assert tag_line(line, rules, field="level") == ["error"]

    def test_json_field_no_match(self):
        rules = parse_tag_rules("error:ERROR")
        line = json.dumps({"level": "INFO", "msg": "ok"})
        assert tag_line(line, rules, field="level") == []

    def test_missing_json_field_no_match(self):
        rules = parse_tag_rules("error:ERROR")
        line = json.dumps({"msg": "no level here"})
        assert tag_line(line, rules, field="level") == []

    def test_invalid_json_with_field_falls_back_to_full_line(self):
        """When a field is requested but the line is not valid JSON,
        tag_line should fall back to matching against the raw line."""
        rules = parse_tag_rules("error:ERROR")
        line = "not json but contains ERROR"
        assert tag_line(line, rules, field="level") == ["error"]

    def test_duplicate_tags_not_returned(self):
        """A tag should appear at most once even if multiple rules share the
        same tag name and both match."""
        rules = [
            {"tag": "error", "pattern": "ERROR"},
            {"tag": "error", "pattern": "ERR"},
        ]
        tags = tag_line("ERROR and ERR in the same line", rules)
        assert tags.count("error") == 1


# ---------------------------------------------------------------------------
# inject_tags
# ---------------
