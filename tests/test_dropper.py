"""Tests for logdrift.dropper and logdrift.drop_output."""
from __future__ import annotations

import json

import pytest

from logdrift.dropper import parse_drop_fields, drop_json_fields, drop_line
from logdrift.drop_output import make_drop_fields, apply_drop


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _line(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# parse_drop_fields
# ---------------------------------------------------------------------------

class TestParseDropFields:
    def test_none_returns_empty(self):
        assert parse_drop_fields(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_drop_fields("") == []

    def test_whitespace_only_returns_empty(self):
        assert parse_drop_fields("   ") == []

    def test_single_field(self):
        assert parse_drop_fields("password") == ["password"]

    def test_multiple_fields(self):
        assert parse_drop_fields("a,b,c") == ["a", "b", "c"]

    def test_strips_whitespace(self):
        assert parse_drop_fields(" x , y ") == ["x", "y"]

    def test_skips_blank_segments(self):
        assert parse_drop_fields("a,,b") == ["a", "b"]


# ---------------------------------------------------------------------------
# drop_json_fields
# ---------------------------------------------------------------------------

class TestDropJsonFields:
    def test_removes_specified_key(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = drop_json_fields(data, ["b"])
        assert result == {"a": 1, "c": 3}

    def test_removes_multiple_keys(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = drop_json_fields(data, ["a", "c"])
        assert result == {"b": 2}

    def test_unknown_field_ignored(self):
        data = {"a": 1}
        result = drop_json_fields(data, ["z"])
        assert result == {"a": 1}

    def test_empty_fields_list_returns_copy(self):
        data = {"a": 1, "b": 2}
        result = drop_json_fields(data, [])
        assert result == data
        assert result is not data

    def test_drop_all_fields_returns_empty(self):
        data = {"x": 10}
        result = drop_json_fields(data, ["x"])
        assert result == {}


# ---------------------------------------------------------------------------
# drop_line
# ---------------------------------------------------------------------------

class TestDropLine:
    def test_plain_text_returned_unchanged(self):
        raw = "plain log message"
        assert drop_line(raw, ["field"]) == raw

    def test_empty_fields_returns_original(self):
        raw = _line(level="info", msg="hello")
        assert drop_line(raw, []) == raw

    def test_removes_field_from_json_line(self):
        raw = _line(level="info", secret="abc", msg="ok")
        result = json.loads(drop_line(raw, ["secret"]))
        assert "secret" not in result
        assert result["level"] == "info"

    def test_removes_multiple_fields(self):
        raw = _line(a=1, b=2, c=3)
        result = json.loads(drop_line(raw, ["a", "c"]))
        assert result == {"b": 2}

    def test_unknown_field_no_error(self):
        raw = _line(a=1)
        result = json.loads(drop_line(raw, ["z"]))
        assert result == {"a": 1}


# ---------------------------------------------------------------------------
# drop_output helpers
# ---------------------------------------------------------------------------

def test_make_drop_fields_none_returns_empty():
    assert make_drop_fields(None) == []


def test_make_drop_fields_returns_list():
    assert make_drop_fields("x,y") == ["x", "y"]


def test_apply_drop_no_fields_returns_original():
    raw = _line(a=1, b=2)
    assert apply_drop(raw, []) == raw


def test_apply_drop_removes_field():
    raw = _line(token="secret", msg="hi")
    result = json.loads(apply_drop(raw, ["token"]))
    assert "token" not in result
    assert result["msg"] == "hi"


def test_apply_drop_plain_text_unchanged():
    raw = "not json"
    assert apply_drop(raw, ["field"]) == raw
