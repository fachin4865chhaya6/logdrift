import io
import json
import pytest
from logdrift.validate_output import make_validation_rules, apply_validation


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_validation_rules_none_returns_empty():
    assert make_validation_rules(None) == []


def test_make_validation_rules_returns_rules():
    rules = make_validation_rules("level:INFO")
    assert len(rules) == 1


def test_apply_validation_no_rules_returns_raw():
    raw = _line(level="DEBUG")
    result = apply_validation(raw, [])
    assert result == raw


def test_apply_validation_passing_line_returned():
    rules = make_validation_rules("level:INFO")
    raw = _line(level="INFO")
    result = apply_validation(raw, rules, warn_stream=io.StringIO())
    assert result == raw


def test_apply_validation_failing_line_warns():
    rules = make_validation_rules("level:INFO:bad-level")
    raw = _line(level="DEBUG")
    stream = io.StringIO()
    result = apply_validation(raw, rules, warn_stream=stream)
    assert result == raw
    assert "bad-level" in stream.getvalue()


def test_apply_validation_drop_invalid_returns_none():
    rules = make_validation_rules("level:INFO")
    raw = _line(level="ERROR")
    stream = io.StringIO()
    result = apply_validation(raw, rules, drop_invalid=True, warn_stream=stream)
    assert result is None


def test_apply_validation_drop_invalid_valid_line_kept():
    rules = make_validation_rules("level:INFO")
    raw = _line(level="INFO")
    stream = io.StringIO()
    result = apply_validation(raw, rules, drop_invalid=True, warn_stream=stream)
    assert result == raw
    assert stream.getvalue() == ""
