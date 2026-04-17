"""Tests for logdrift.diff_output."""
import json
from logdrift.diff_output import make_line_differ, record_diff, write_diff_summary


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_line_differ_none_returns_none():
    assert make_line_differ(None) is None


def test_make_line_differ_empty_returns_none():
    assert make_line_differ("") is None


def test_make_line_differ_returns_differ():
    d = make_line_differ("level")
    assert d is not None
    assert d.fields == ["level"]


def test_record_diff_none_differ_is_noop():
    called = []
    record_diff(None, _line(level="info"), callback=called.append)
    assert called == []


def test_record_diff_plain_text_no_callback():
    d = make_line_differ("level")
    called = []
    record_diff(d, "plain text", callback=called.append)
    assert called == []


def test_record_diff_first_line_triggers_callback():
    d = make_line_differ("level")
    called = []
    record_diff(d, _line(level="info"), callback=called.append)
    assert len(called) == 1
    assert "level" in called[0]


def test_record_diff_unchanged_no_callback():
    d = make_line_differ("level")
    record_diff(d, _line(level="info"), callback=lambda _: None)
    called = []
    record_diff(d, _line(level="info"), callback=called.append)
    assert called == []


def test_write_diff_summary_none_is_noop():
    import io
    out = io.StringIO()
    write_diff_summary(None, stream=out)
    assert out.getvalue() == ""


def test_write_diff_summary_writes_stats():
    import io
    d = make_line_differ("level")
    d.diff(_line(level="info"))
    out = io.StringIO()
    write_diff_summary(d, stream=out)
    assert "total=1" in out.getvalue()
    assert "changed=1" in out.getvalue()
