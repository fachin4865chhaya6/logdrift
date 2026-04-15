"""Tests for logdrift.aggregator."""

import json
import pytest

from logdrift.aggregator import Aggregator, parse_aggregate_field


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestAggregator:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            Aggregator("")

    def test_add_returns_bucket_key(self):
        agg = Aggregator("level")
        key = agg.add(_line(level="error", msg="oops"))
        assert key == "error"

    def test_add_plain_text_returns_none(self):
        agg = Aggregator("level")
        key = agg.add("not json at all")
        assert key is None

    def test_add_missing_field_returns_none(self):
        agg = Aggregator("level")
        key = agg.add(_line(msg="no level here"))
        assert key is None

    def test_counts_accumulate(self):
        agg = Aggregator("level")
        for _ in range(3):
            agg.add(_line(level="info"))
        agg.add(_line(level="error"))
        assert agg.counts() == {"info": 3, "error": 1}

    def test_total_includes_all_lines(self):
        agg = Aggregator("level")
        agg.add(_line(level="info"))
        agg.add("plain text")
        agg.add(_line(msg="no level"))
        assert agg.total == 3

    def test_top_returns_sorted_descending(self):
        agg = Aggregator("level")
        for _ in range(5):
            agg.add(_line(level="debug"))
        for _ in range(2):
            agg.add(_line(level="error"))
        top = agg.top(2)
        assert top[0] == ("debug", 5)
        assert top[1] == ("error", 2)

    def test_top_n_capped_at_available_buckets(self):
        agg = Aggregator("level")
        agg.add(_line(level="info"))
        assert len(agg.top(100)) == 1

    def test_reset_clears_state(self):
        agg = Aggregator("level")
        agg.add(_line(level="info"))
        agg.reset()
        assert agg.counts() == {}
        assert agg.total == 0

    def test_format_summary_no_data(self):
        agg = Aggregator("level")
        summary = agg.format_summary()
        assert "no data" in summary

    def test_format_summary_contains_field_and_counts(self):
        agg = Aggregator("level")
        agg.add(_line(level="warn"))
        agg.add(_line(level="warn"))
        agg.add(_line(level="error"))
        summary = agg.format_summary()
        assert "level" in summary
        assert "warn" in summary
        assert "error" in summary
        assert "3" in summary

    def test_nested_field_path(self):
        agg = Aggregator("context.env")
        agg.add(json.dumps({"context": {"env": "prod"}, "msg": "ok"}))
        assert agg.counts() == {"prod": 1}


class TestParseAggregateField:
    def test_none_returns_none(self):
        assert parse_aggregate_field(None) is None

    def test_empty_string_returns_none(self):
        assert parse_aggregate_field("") is None

    def test_whitespace_only_returns_none(self):
        assert parse_aggregate_field("   ") is None

    def test_valid_field_returned_stripped(self):
        assert parse_aggregate_field("  level  ") == "level"

    def test_dotted_path_preserved(self):
        assert parse_aggregate_field("context.env") == "context.env"
