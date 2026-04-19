from __future__ import annotations

import json
import pytest

from logdrift.field_selector import parse_field_selector, select_fields, select_line


class TestParseFieldSelector:
    def test_none_returns_empty(self):
        assert parse_field_selector(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_field_selector("") == []

    def test_whitespace_returns_empty(self):
        assert parse_field_selector("   ") == []

    def test_single_field(self):
        assert parse_field_selector("level") == ["level"]

    def test_multiple_fields(self):
        assert parse_field_selector("level,message,ts") == ["level", "message", "ts"]

    def test_strips_whitespace_around_fields(self):
        assert parse_field_selector(" level , message ") == ["level", "message"]

    def test_ignores_empty_segments(self):
        assert parse_field_selector("level,,message") == ["level", "message"]


class TestSelectFields:
    def test_empty_fields_returns_full_dict(self):
        d = {"a": 1, "b": 2}
        assert select_fields(d, []) == d

    def test_keeps_requested_fields(self):
        d = {"level": "info", "msg": "hi", "ts": 1}
        assert select_fields(d, ["level", "ts"]) == {"level": "info", "ts": 1}

    def test_missing_fields_silently_omitted(self):
        d = {"level": "info"}
        assert select_fields(d, ["level", "missing"]) == {"level": "info"}

    def test_all_fields_missing_returns_empty(self):
        d = {"a": 1}
        assert select_fields(d, ["x", "y"]) == {}


class TestSelectLine:
    def test_no_fields_returns_unchanged(self):
        raw = '{"a":1}'
        parsed = {"a": 1}
        r, p = select_line(raw, parsed, [])
        assert r == raw
        assert p == parsed

    def test_none_parsed_returns_unchanged(self):
        raw = "plain text"
        r, p = select_line(raw, None, ["level"])
        assert r == raw
        assert p is None

    def test_filters_fields_and_updates_raw(self):
        parsed = {"level": "info", "msg": "hello", "ts": 42}
        raw = json.dumps(parsed)
        r, p = select_line(raw, parsed, ["level", "ts"])
        assert p == {"level": "info", "ts": 42}
        assert json.loads(r) == {"level": "info", "ts": 42}

    def test_all_fields_missing_returns_empty_json(self):
        parsed = {"a": 1}
        r, p = select_line(json.dumps(parsed), parsed, ["x"])
        assert p == {}
        assert json.loads(r) == {}
