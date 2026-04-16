"""Tests for logdrift.tracer."""
import json
import pytest
from logdrift.tracer import TraceCollector, parse_trace_field


def _line(trace_id, msg="hello", level="info"):
    return json.dumps({"trace_id": trace_id, "msg": msg, "level": level})


class TestParseTraceField:
    def test_valid_field_returned(self):
        assert parse_trace_field("trace_id") == "trace_id"

    def test_strips_whitespace(self):
        assert parse_trace_field("  trace_id  ") == "trace_id"

    def test_none_raises(self):
        with pytest.raises(ValueError):
            parse_trace_field(None)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_trace_field("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            parse_trace_field("   ")


class TestTraceCollector:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            TraceCollector(trace_field="")

    def test_zero_max_traces_raises(self):
        with pytest.raises(ValueError):
            TraceCollector(trace_field="trace_id", max_traces=0)

    def test_add_plain_text_returns_none(self):
        tc = TraceCollector(trace_field="trace_id")
        assert tc.add("plain text") is None

    def test_add_missing_field_returns_none(self):
        tc = TraceCollector(trace_field="trace_id")
        line = json.dumps({"msg": "no trace here"})
        assert tc.add(line) is None

    def test_add_returns_trace_id(self):
        tc = TraceCollector(trace_field="trace_id")
        key = tc.add(_line("abc-123"))
        assert key == "abc-123"

    def test_total_counts_unique_ids(self):
        tc = TraceCollector(trace_field="trace_id")
        tc.add(_line("id-1"))
        tc.add(_line("id-2"))
        tc.add(_line("id-1"))
        assert tc.total == 2

    def test_get_trace_returns_lines(self):
        tc = TraceCollector(trace_field="trace_id")
        l1 = _line("t1", msg="first")
        l2 = _line("t1", msg="second")
        tc.add(l1)
        tc.add(l2)
        result = tc.get_trace("t1")
        assert result == [l1, l2]

    def test_get_trace_missing_returns_empty(self):
        tc = TraceCollector(trace_field="trace_id")
        assert tc.get_trace("nonexistent") == []

    def test_all_trace_ids(self):
        tc = TraceCollector(trace_field="trace_id")
        tc.add(_line("a"))
        tc.add(_line("b"))
        assert set(tc.all_trace_ids()) == {"a", "b"}

    def test_max_traces_evicts_oldest(self):
        tc = TraceCollector(trace_field="trace_id", max_traces=2)
        tc.add(_line("first"))
        tc.add(_line("second"))
        tc.add(_line("third"))
        assert tc.total == 2
        assert "first" not in tc.all_trace_ids()

    def test_format_summary_contains_trace_id(self):
        tc = TraceCollector(trace_field="trace_id")
        tc.add(_line("xyz"))
        summary = tc.format_summary()
        assert "xyz" in summary
        assert "1 line(s)" in summary
