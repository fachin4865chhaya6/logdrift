from __future__ import annotations

import json
import pytest

from logdrift.field_output import make_field_selector, apply_field_selection


def _line(d: dict) -> tuple[str, dict]:
    raw = json.dumps(d)
    return raw, d


def test_make_field_selector_none_returns_empty():
    assert make_field_selector(None) == []


def test_make_field_selector_returns_list():
    assert make_field_selector("level,msg") == ["level", "msg"]


def test_make_field_selector_strips_whitespace():
    assert make_field_selector("level, msg , ts") == ["level", "msg", "ts"]


def test_make_field_selector_single_field():
    assert make_field_selector("level") == ["level"]


def test_apply_field_selection_no_fields_unchanged():
    raw, parsed = _line({"a": 1, "b": 2})
    r, p = apply_field_selection(raw, parsed, [])
    assert r == raw
    assert p == parsed


def test_apply_field_selection_filters_correctly():
    raw, parsed = _line({"level": "warn", "msg": "oops", "ts": 99})
    r, p = apply_field_selection(raw, parsed, ["level"])
    assert p == {"level": "warn"}
    assert json.loads(r) == {"level": "warn"}


def test_apply_field_selection_plain_text_unchanged():
    r, p = apply_field_selection("plain", None, ["level"])
    assert r == "plain"
    assert p is None


def test_apply_field_selection_missing_fields_omitted():
    raw, parsed = _line({"a": 1})
    r, p = apply_field_selection(raw, parsed, ["b"])
    assert p == {}


def test_apply_field_selection_multiple_fields():
    raw, parsed = _line({"level": "info", "msg": "hello", "ts": 123, "caller": "main.go"})
    r, p = apply_field_selection(raw, parsed, ["level", "msg"])
    assert p == {"level": "info", "msg": "hello"}
    assert json.loads(r) == {"level": "info", "msg": "hello"}
