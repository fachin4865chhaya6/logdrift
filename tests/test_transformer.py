"""Tests for logdrift.transformer."""

from __future__ import annotations

import json

import pytest

from logdrift.transformer import parse_field_map, transform_fields, transform_line


class TestParseFieldMap:
    def test_none_returns_empty(self):
        assert parse_field_map(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_field_map("") == {}

    def test_single_rename(self):
        assert parse_field_map("msg=message") == {"msg": "message"}

    def test_multiple_renames(self):
        result = parse_field_map("msg=message,ts=timestamp")
        assert result == {"msg": "message", "ts": "timestamp"}

    def test_drop_field_empty_target(self):
        assert parse_field_map("debug=") == {"debug": ""}

    def test_whitespace_around_entries_is_stripped(self):
        assert parse_field_map(" msg = message ") == {"msg": "message"}

    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match="Invalid field map entry"):
            parse_field_map("msgmessage")

    def test_empty_source_field_raises(self):
        with pytest.raises(ValueError, match="Empty source field name"):
            parse_field_map("=message")

    def test_trailing_comma_ignored(self):
        result = parse_field_map("msg=message,")
        assert result == {"msg": "message"}


class TestTransformFields:
    def test_empty_map_returns_data_unchanged(self):
        data = {"msg": "hello", "level": "info"}
        assert transform_fields(data, {}) == data

    def test_rename_single_field(self):
        data = {"msg": "hello", "level": "info"}
        result = transform_fields(data, {"msg": "message"})
        assert result == {"message": "hello", "level": "info"}

    def test_drop_field(self):
        data = {"msg": "hello", "debug": True}
        result = transform_fields(data, {"debug": ""})
        assert result == {"msg": "hello"}
        assert "debug" not in result

    def test_untouched_fields_preserved(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = transform_fields(data, {"a": "alpha"})
        assert result["b"] == 2
        assert result["c"] == 3

    def test_rename_and_drop_together(self):
        data = {"msg": "hi", "ts": 123, "noise": True}
        result = transform_fields(data, {"msg": "message", "noise": ""})
        assert "message" in result
        assert "noise" not in result
        assert result["ts"] == 123


class TestTransformLine:
    def test_plain_text_returned_unchanged(self):
        line = "plain log line"
        assert transform_line(line, {"msg": "message"}) == line

    def test_empty_line_returned_unchanged(self):
        assert transform_line("", {"msg": "message"}) == ""

    def test_empty_map_returns_line_unchanged(self):
        line = json.dumps({"msg": "hi"})
        assert transform_line(line, {}) == line

    def test_json_line_renamed(self):
        line = json.dumps({"msg": "hello", "level": "info"})
        result = transform_line(line, {"msg": "message"})
        data = json.loads(result)
        assert data["message"] == "hello"
        assert "msg" not in data

    def test_json_line_field_dropped(self):
        line = json.dumps({"msg": "hello", "debug": True})
        result = transform_line(line, {"debug": ""})
        data = json.loads(result)
        assert "debug" not in data
        assert data["msg"] == "hello"

    def test_json_array_returned_unchanged(self):
        line = json.dumps([1, 2, 3])
        assert transform_line(line, {"a": "b"}) == line
