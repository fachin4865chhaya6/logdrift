"""Tests for logdrift/output.py"""

import io
import pytest

from logdrift.output import write_line, write_summary, run_output
from logdrift.stats import LogStats


JSON_LINE = '{"level": "ERROR", "message": "disk full"}'
PLAIN_LINE = "plain text log entry"


class TestWriteLine:
    def _make_stream(self):
        return io.StringIO()

    def test_matched_line_written_to_stream(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(JSON_LINE, matched=True, stats=stats, stream=stream, color=False)
        output = stream.getvalue()
        assert "disk full" in output or JSON_LINE in output

    def test_unmatched_line_not_written(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(JSON_LINE, matched=False, stats=stats, stream=stream, color=False)
        assert stream.getvalue() == ""

    def test_stats_updated_for_matched(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(JSON_LINE, matched=True, stats=stats, stream=stream, color=False)
        assert stats.total == 1
        assert stats.matched == 1

    def test_stats_updated_for_unmatched(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(JSON_LINE, matched=False, stats=stats, stream=stream, color=False)
        assert stats.total == 1
        assert stats.matched == 0

    def test_keyword_highlighted_in_output(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(
            PLAIN_LINE,
            matched=True,
            stats=stats,
            stream=stream,
            color=False,
            keywords=["plain"],
        )
        output = stream.getvalue()
        assert "plain" in output

    def test_newline_appended(self):
        stats = LogStats()
        stream = self._make_stream()
        write_line(PLAIN_LINE, matched=True, stats=stats, stream=stream, color=False)
        assert stream.getvalue().endswith("\n")


class TestWriteSummary:
    def test_summary_written_to_stream(self):
        stats = LogStats()
        stream = io.StringIO()
        write_summary(stats, stream, color=False)
        output = stream.getvalue()
        assert len(output) > 0

    def test_summary_contains_totals(self):
        stats = LogStats()
        stats.total = 10
        stats.matched = 7
        stream = io.StringIO()
        write_summary(stats, stream, color=False)
        output = stream.getvalue()
        assert "10" in output
        assert "7" in output


class TestRunOutput:
    def test_returns_log_stats(self):
        lines = [(JSON_LINE, True), (PLAIN_LINE, False)]
        stats = run_output(lines, color=False)
        assert isinstance(stats, LogStats)
        assert stats.total == 2
        assert stats.matched == 1

    def test_writes_to_file(self, tmp_path):
        out_file = tmp_path / "out.log"
        lines = [(PLAIN_LINE, True)]
        run_output(lines, output_path=str(out_file), color=False)
        content = out_file.read_text()
        assert PLAIN_LINE in content

    def test_show_summary_appends_stats(self, tmp_path):
        out_file = tmp_path / "out.log"
        lines = [(PLAIN_LINE, True)]
        run_output(lines, output_path=str(out_file), color=False, show_summary=True)
        content = out_file.read_text()
        assert "1" in content
