"""Tests for logdrift.profile_output."""
import json
import io
from logdrift.profiler import FieldProfiler
from logdrift.profile_output import (
    make_field_profiler,
    record_for_profiling,
    write_profile_summary,
)


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_make_field_profiler_none_returns_none():
    assert make_field_profiler(None) is None


def test_make_field_profiler_returns_profiler():
    p = make_field_profiler("level")
    assert isinstance(p, FieldProfiler)


def test_record_for_profiling_none_profiler_is_noop():
    record_for_profiling(None, _line(level="info"))  # should not raise


def test_record_for_profiling_increments_total():
    p = make_field_profiler("level")
    record_for_profiling(p, _line(level="info"))
    assert p.total == 1


def test_record_for_profiling_plain_text_ignored():
    p = make_field_profiler("level")
    record_for_profiling(p, "not json")
    assert p.total == 0


def test_write_profile_summary_none_profiler_writes_nothing():
    stream = io.StringIO()
    write_profile_summary(None, stream=stream)
    assert stream.getvalue() == ""


def test_write_profile_summary_empty_profiler_writes_nothing():
    p = make_field_profiler("level")
    stream = io.StringIO()
    write_profile_summary(p, stream=stream)
    assert stream.getvalue() == ""


def test_write_profile_summary_writes_summary():
    p = make_field_profiler("level")
    record_for_profiling(p, _line(level="info"))
    stream = io.StringIO()
    write_profile_summary(p, stream=stream)
    output = stream.getvalue()
    assert "level" in output
    assert "info" in output
