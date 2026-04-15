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


# ---------------------------------------------------------------------------
# inject_tags
# ---------------------------------------------------------------------------

class TestInjectTags:
    def test_no_tags_returns_line_unchanged(self):
        line = "plain text"
        assert inject_tags(line, []) == line

    def test_plain_text_gets_prefix(self):
        result = inject_tags("hello world", ["error", "critical"])
        assert result == "[error,critical] hello world"

    def test_json_gets_tags_field(self):
        line = json.dumps({"msg": "boom"})
        result = inject_tags(line, ["error"])
        parsed = json.loads(result)
        assert parsed["_tags"] == ["error"]
        assert parsed["msg"] == "boom"

    def test_json_single_tag(self):
        line = json.dumps({"level": "ERROR"})
        result = inject_tags(line, ["error"])
        assert json.loads(result)["_tags"] == ["error"]
