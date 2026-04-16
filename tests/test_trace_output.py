"""Tests for logdrift.trace_output."""
import json
from logdrift.trace_output import (
    make_trace_collector,
    record_for_tracing,
    write_trace_summary,
)


def _line(trace_id, msg="hi"):
    return json.dumps({"trace_id": trace_id, "msg": msg})


def test_make_trace_collector_none_returns_none():
    assert make_trace_collector(None) is None


def test_make_trace_collector_empty_returns_none():
    assert make_trace_collector("") is None


def test_make_trace_collector_returns_collector():
    tc = make_trace_collector("trace_id")
    assert tc is not None
    assert tc.trace_field == "trace_id"


def test_make_trace_collector_passes_max_traces():
    tc = make_trace_collector("trace_id", max_traces=5)
    assert tc.max_traces == 5


def test_record_for_tracing_none_collector_is_noop():
    assert record_for_tracing(None, _line("x")) is None


def test_record_for_tracing_returns_key():
    tc = make_trace_collector("trace_id")
    key = record_for_tracing(tc, _line("abc"))
    assert key == "abc"


def test_record_for_tracing_increments_total():
    tc = make_trace_collector("trace_id")
    record_for_tracing(tc, _line("t1"))
    record_for_tracing(tc, _line("t2"))
    assert tc.total == 2


def test_write_trace_summary_none_is_noop():
    write_trace_summary(None)  # should not raise


def test_write_trace_summary_calls_callback():
    tc = make_trace_collector("trace_id")
    record_for_tracing(tc, _line("r1"))
    record_for_tracing(tc, _line("r1"))
    record_for_tracing(tc, _line("r2"))
    collected = {}

    def cb(trace_id, lines):
        collected[trace_id] = lines

    write_trace_summary(tc, callback=cb)
    assert "r1" in collected
    assert len(collected["r1"]) == 2
    assert "r2" in collected
