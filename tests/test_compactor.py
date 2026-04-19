"""Tests for logdrift.compactor."""
import json

import pytest

from logdrift.compactor import (
    compact_json_fields,
    compact_line,
    parse_compact_fields,
)


class TestParseCompactFields:
    def test_none_returns_empty(self):
        assert parse_compact_fields(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_compact_fields("") == []

    def test_single_field(self):
        assert parse_compact_fields("password") == ["password"]

    def test_multiple_fields(self):
        assert parse_compact_fields("token,secret,key") == ["token", "secret", "key"]

    def test_strips_whitespace(self):
        assert parse_compact_fields(" a , b ") == ["a", "b"]

    def test_ignores_empty_segments(self):
        assert parse_compact_fields("a,,b") == ["a", "b"]


class TestCompactJsonFields:
    def test_removes_listed_keys(self):
        data = {"level": "info", "secret": "x", "msg": "hi"}
        result = compact_json_fields(data, ["secret"])
        assert "secret" not in result
        assert result["level"] == "info"

    def test_missing_key_is_noop(self):
        data = {"a": 1}
        assert compact_json_fields(data, ["z"]) == {"a": 1}

    def test_empty_fields_returns_copy(self):
        data = {"a": 1, "b": 2}
        result = compact_json_fields(data, [])
        assert result == data
        assert result is not data

    def test_removes_multiple_keys(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = compact_json_fields(data, ["a", "c"])
        assert result == {"b": 2}


class TestCompactLine:
    def _json(self, **kw) -> str:
        return json.dumps(kw)

    def test_plain_text_unchanged(self):
        assert compact_line("hello world", ["secret"]) == "hello world"

    def test_no_fields_returns_original(self):
        raw = self._json(level="info", msg="ok")
        assert compact_line(raw, []) == raw

    def test_removes_field_from_json(self):
        raw = self._json(level="info", token="abc", msg="ok")
        result = json.loads(compact_line(raw, ["token"]))
        assert "token" not in result
        assert result["level"] == "info"

    def test_removes_multiple_fields(self):
        raw = self._json(a=1, b=2, c=3)
        result = json.loads(compact_line(raw, ["a", "c"]))
        assert result == {"b": 2}

    def test_nonexistent_field_is_noop(self):
        raw = self._json(level="debug", msg="test")
        result = json.loads(compact_line(raw, ["ghost"]))
        assert result == {"level": "debug", "msg": "test"}
