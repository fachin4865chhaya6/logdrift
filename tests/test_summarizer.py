import pytest
from logdrift.summarizer import (
    LineSummarizer,
    parse_summarize_field,
    make_summarizer,
)


class TestParseSummarizeField:
    def test_none_returns_none(self):
        assert parse_summarize_field(None) is None

    def test_empty_string_returns_none(self):
        assert parse_summarize_field("") is None

    def test_whitespace_returns_none(self):
        assert parse_summarize_field("   ") is None

    def test_valid_field_returned(self):
        assert parse_summarize_field("level") == "level"

    def test_strips_whitespace(self):
        assert parse_summarize_field("  service  ") == "service"


class TestLineSummarizer:
    def test_invalid_max_samples_raises(self):
        with pytest.raises(ValueError):
            LineSummarizer(max_samples=0)

    def test_empty_bucket_raises(self):
        s = LineSummarizer()
        with pytest.raises(ValueError):
            s.add("", "some line")

    def test_initial_state(self):
        s = LineSummarizer()
        assert s.total == 0
        assert s.buckets == {}

    def test_add_increments_total(self):
        s = LineSummarizer()
        s.add("error", "line1")
        assert s.total == 1

    def test_add_increments_bucket_count(self):
        s = LineSummarizer()
        s.add("error", "line1")
        s.add("error", "line2")
        assert s.buckets["error"] == 2

    def test_multiple_buckets_tracked(self):
        s = LineSummarizer()
        s.add("info", "a")
        s.add("error", "b")
        assert s.buckets["info"] == 1
        assert s.buckets["error"] == 1

    def test_samples_collected(self):
        s = LineSummarizer(max_samples=3)
        for i in range(5):
            s.add("warn", f"line{i}")
        samples = s.get_samples("warn")
        assert len(samples) == 3
        assert samples[0] == "line0"

    def test_get_samples_unknown_bucket(self):
        s = LineSummarizer()
        assert s.get_samples("missing") == []

    def test_format_summary_no_data(self):
        s = LineSummarizer()
        assert "No data" in s.format_summary()

    def test_format_summary_contains_bucket(self):
        s = LineSummarizer()
        s.add("error", "something failed")
        summary = s.format_summary()
        assert "error" in summary
        assert "something failed" in summary

    def test_format_summary_truncates_long_lines(self):
        s = LineSummarizer()
        long_line = "x" * 100
        s.add("debug", long_line)
        summary = s.format_summary()
        assert "..." in summary


class TestMakeSummarizer:
    def test_none_returns_none(self):
        assert make_summarizer(None) is None

    def test_empty_returns_none(self):
        assert make_summarizer("") is None

    def test_valid_field_returns_summarizer(self):
        result = make_summarizer("level")
        assert isinstance(result, LineSummarizer)

    def test_max_samples_passed(self):
        result = make_summarizer("level", max_samples=2)
        assert result.max_samples == 2
