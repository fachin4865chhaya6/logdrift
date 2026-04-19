"""Tests for logdrift.pinner and logdrift.pin_output."""
import json
import pytest

from logdrift.pinner import FieldPinner, parse_pin_fields, pin_json_fields, pin_line
from logdrift.pin_output import make_field_pinner, apply_pinning


# --- parse_pin_fields ---

def test_none_returns_empty():
    assert parse_pin_fields(None) == []

def test_empty_string_returns_empty():
    assert parse_pin_fields("") == []

def test_whitespace_returns_empty():
    assert parse_pin_fields("   ") == []

def test_single_field():
    assert parse_pin_fields("level") == ["level"]

def test_multiple_fields():
    assert parse_pin_fields("level,ts,msg") == ["level", "ts", "msg"]

def test_strips_whitespace():
    assert parse_pin_fields(" level , ts ") == ["level", "ts"]


# --- FieldPinner ---

def test_empty_fields_raises():
    with pytest.raises(ValueError):
        FieldPinner(pin_fields=[])

def test_reorder_pins_first():
    pinner = FieldPinner(pin_fields=["level", "ts"])
    data = {"msg": "hello", "ts": 1, "level": "info"}
    result = pinner.reorder(data)
    keys = list(result.keys())
    assert keys[0] == "level"
    assert keys[1] == "ts"
    assert "msg" in keys

def test_reorder_missing_pin_field_skipped():
    pinner = FieldPinner(pin_fields=["level", "missing"])
    data = {"msg": "hi", "level": "warn"}
    result = pinner.reorder(data)
    assert list(result.keys())[0] == "level"
    assert "missing" not in result

def test_reorder_preserves_all_fields():
    pinner = FieldPinner(pin_fields=["a"])
    data = {"b": 2, "a": 1, "c": 3}
    result = pinner.reorder(data)
    assert set(result.keys()) == {"a", "b", "c"}


# --- pin_json_fields ---

def test_plain_text_unchanged():
    pinner = FieldPinner(pin_fields=["level"])
    assert pin_json_fields("not json", pinner) == "not json"

def test_json_array_unchanged():
    pinner = FieldPinner(pin_fields=["level"])
    line = json.dumps([1, 2, 3])
    assert pin_json_fields(line, pinner) == line

def test_valid_json_reordered():
    pinner = FieldPinner(pin_fields=["level"])
    line = json.dumps({"msg": "hi", "level": "info"})
    result = json.loads(pin_json_fields(line, pinner))
    assert list(result.keys())[0] == "level"


# --- pin_line ---

def test_none_pinner_returns_raw():
    assert pin_line("anything", None) == "anything"

def test_pin_line_applies_pinner():
    pinner = FieldPinner(pin_fields=["ts"])
    line = json.dumps({"msg": "ok", "ts": 99})
    result = json.loads(pin_line(line, pinner))
    assert list(result.keys())[0] == "ts"


# --- pin_output helpers ---

def test_make_field_pinner_none_returns_none():
    assert make_field_pinner(None) is None

def test_make_field_pinner_empty_returns_none():
    assert make_field_pinner("") is None

def test_make_field_pinner_returns_pinner():
    p = make_field_pinner("level,ts")
    assert isinstance(p, FieldPinner)
    assert p.pin_fields == ["level", "ts"]

def test_apply_pinning_no_pinner():
    assert apply_pinning("raw", None) == "raw"

def test_apply_pinning_with_pinner():
    p = make_field_pinner("level")
    line = json.dumps({"msg": "x", "level": "debug"})
    result = json.loads(apply_pinning(line, p))
    assert list(result.keys())[0] == "level"
