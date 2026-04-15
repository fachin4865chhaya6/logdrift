"""Tests for logdrift.stats module."""

import pytest
from logdrift.stats import LogStats


class TestLogStats:
    def test_initial_state(self):
        stats = LogStats()
        assert stats.total_lines == 0
        assert stats.matched_lines == 0
        assert stats.skipped_lines == 0
        assert stats.error_count == 0
        assert len(stats.level_counts) == 0

    def test_record_matched_line(self):
        stats = LogStats()
        stats.record_line(matched=True, level="INFO")
        assert stats.total_lines == 1
        assert stats.matched_lines == 1
        assert stats.skipped_lines == 0

    def test_record_skipped_line(self):
        stats = LogStats()
        stats.record_line(matched=False)
        assert stats.total_lines == 1
        assert stats.matched_lines == 0
        assert stats.skipped_lines == 1

    def test_level_counts_incremented(self):
        stats = LogStats()
        stats.record_line(matched=True, level="info")
        stats.record_line(matched=True, level="INFO")
        stats.record_line(matched=True, level="warn")
        assert stats.level_counts["INFO"] == 2
        assert stats.level_counts["WARN"] == 1

    def test_error_count_for_error_level(self):
        stats = LogStats()
        stats.record_line(matched=True, level="ERROR")
        stats.record_line(matched=True, level="critical")
        stats.record_line(matched=True, level="FATAL")
        assert stats.error_count == 3

    def test_error_count_not_incremented_for_info(self):
        stats = LogStats()
        stats.record_line(matched=True, level="INFO")
        assert stats.error_count == 0

    def test_match_rate_zero_when_no_lines(self):
        stats = LogStats()
        assert stats.match_rate() == 0.0

    def test_match_rate_calculation(self):
        stats = LogStats()
        stats.record_line(matched=True)
        stats.record_line(matched=False)
        assert stats.match_rate() == 0.5

    def test_summary_keys(self):
        stats = LogStats()
        summary = stats.summary()
        assert "total_lines" in summary
        assert "matched_lines" in summary
        assert "skipped_lines" in summary
        assert "match_rate" in summary
        assert "error_count" in summary
        assert "level_counts" in summary

    def test_format_summary_contains_totals(self):
        stats = LogStats()
        stats.record_line(matched=True, level="INFO")
        stats.record_line(matched=False)
        output = stats.format_summary()
        assert "Total lines" in output
        assert "2" in output
        assert "Match rate" in output

    def test_format_summary_includes_level_counts(self):
        stats = LogStats()
        stats.record_line(matched=True, level="DEBUG")
        output = stats.format_summary()
        assert "DEBUG" in output
