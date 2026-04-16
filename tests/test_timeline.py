"""Tests for logdrift.timeline."""
import json
import pytest
from logdrift.timeline import Timeline, parse_timeline_args


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestTimeline:
    def test_invalid_bucket_raises(self):
        with pytest.raises(ValueError, match="bucket_seconds"):
            Timeline(bucket_seconds=0, time_field="ts")

    def test_empty_time_field_raises(self):
        with pytest.raises(ValueError, match="time_field"):
            Timeline(bucket_seconds=60, time_field="")

    def test_add_plain_text_returns_none(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        assert t.add("not json") is None

    def test_add_missing_field_returns_none(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        assert t.add(_line(level="info")) is None

    def test_add_non_numeric_field_returns_none(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        assert t.add(_line(ts="not-a-number")) is None

    def test_add_returns_bucket_key(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        key = t.add(_line(ts=90))
        assert key == 60

    def test_bucket_incremented(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        t.add(_line(ts=90))
        t.add(_line(ts=100))
        assert t.buckets[60] == 2

    def test_multiple_buckets(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        t.add(_line(ts=30))
        t.add(_line(ts=90))
        t.add(_line(ts=150))
        assert len(t.buckets) == 3

    def test_float_timestamp(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        key = t.add(_line(ts=61.9))
        assert key == 60

    def test_format_summary_no_data(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        result = t.format_summary()
        assert result == ["timeline: no data"]

    def test_format_summary_has_header(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        t.add(_line(ts=30))
        lines = t.format_summary()
        assert lines[0] == "timeline summary:"
        assert len(lines) == 2

    def test_format_summary_sorted(self):
        t = Timeline(bucket_seconds=60, time_field="ts")
        t.add(_line(ts=180))
        t.add(_line(ts=60))
        lines = t.format_summary()
        assert "60" in lines[1]
        assert "180" in lines[2]


class TestParseTimelineArgs:
    def test_none_field_returns_none(self):
        assert parse_timeline_args(None, 60) is None

    def test_empty_field_returns_none(self):
        assert parse_timeline_args("", 60) is None

    def test_returns_timeline(self):
        t = parse_timeline_args("ts", 30)
        assert isinstance(t, Timeline)
        assert t.bucket_seconds == 30
        assert t.time_field == "ts"

    def test_default_bucket_seconds(self):
        t = parse_timeline_args("ts", None)
        assert t.bucket_seconds == 60
