"""Tests for logdrift.redactor."""

import pytest
from logdrift.redactor import (
    DEFAULT_MASK,
    parse_redact_fields,
    parse_redact_patterns,
    redact_json_fields,
    redact_patterns,
    redact_line,
)


class TestParseRedactFields:
    def test_none_returns_empty(self):
        assert parse_redact_fields(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_redact_fields("") == []

    def test_single_field(self):
        assert parse_redact_fields("password") == ["password"]

    def test_multiple_fields(self):
        assert parse_redact_fields("password,token,secret") == ["password", "token", "secret"]

    def test_strips_whitespace(self):
        assert parse_redact_fields(" email , token ") == ["email", "token"]


class TestParseRedactPatterns:
    def test_none_returns_empty(self):
        assert parse_redact_patterns(None) == []

    def test_valid_pattern_name(self):
        assert parse_redact_patterns("email") == ["email"]

    def test_multiple_patterns(self):
        assert parse_redact_patterns("email,ipv4") == ["email", "ipv4"]


class TestRedactJsonFields:
    def test_replaces_matching_field(self):
        data = {"user": "alice", "password": "s3cr3t"}
        result = redact_json_fields(data, ["password"])
        assert result["password"] == DEFAULT_MASK
        assert result["user"] == "alice"

    def test_missing_field_is_ignored(self):
        data = {"user": "alice"}
        result = redact_json_fields(data, ["password"])
        assert "password" not in result

    def test_empty_fields_returns_copy(self):
        data = {"user": "alice"}
        result = redact_json_fields(data, [])
        assert result == data
        assert result is not data

    def test_custom_mask(self):
        data = {"token": "abc123"}
        result = redact_json_fields(data, ["token"], mask="[HIDDEN]")
        assert result["token"] == "[HIDDEN]"


class TestRedactPatterns:
    def test_redacts_email(self):
        text = "user alice@example.com logged in"
        result = redact_patterns(text, ["email"])
        assert "alice@example.com" not in result
        assert DEFAULT_MASK in result

    def test_redacts_ipv4(self):
        text = "request from 192.168.1.1 received"
        result = redact_patterns(text, ["ipv4"])
        assert "192.168.1.1" not in result

    def test_unknown_pattern_ignored(self):
        text = "some log line"
        result = redact_patterns(text, ["unknown_pattern"])
        assert result == text

    def test_empty_patterns_unchanged(self):
        text = "no change expected"
        assert redact_patterns(text, []) == text


class TestRedactLine:
    def test_redacts_json_field(self):
        import json
        parsed = {"level": "info", "password": "hunter2"}
        line = json.dumps(parsed)
        new_line, new_parsed = redact_line(line, parsed, ["password"], [])
        assert new_parsed["password"] == DEFAULT_MASK
        assert "hunter2" not in new_line

    def test_plain_text_pattern_redaction(self):
        line = "contact me at test@test.com"
        new_line, new_parsed = redact_line(line, None, [], ["email"])
        assert "test@test.com" not in new_line
        assert new_parsed is None

    def test_no_redaction_returns_original(self):
        line = "nothing to redact"
        new_line, new_parsed = redact_line(line, None, [], [])
        assert new_line == line
        assert new_parsed is None
