"""Tests for logdrift.output (including redaction integration)."""

import io
import json
import pytest
from unittest.mock import patch

from logdrift.output import write_line, write_summary, run_output
from logdrift.stats import LogStats


def _make_stream():
    return io.StringIO()


class TestWriteLine:
    def _stats(self):
        return LogStats()

    def test_matched_line_written_to_stream(self):
        stream = _make_stream()
        stats = self._stats()
        write_line('{"msg": "ok"}', stream, stats, [], [], [], matched=True,
                   parsed={"msg": "ok"})
        assert stream.getvalue().strip() != ""

    def test_unmatched_line_not_written(self):
        stream = _make_stream()
        stats = self._stats()
        write_line("some line", stream, stats, [], [], [], matched=False, parsed=None)
        assert stream.getvalue() == ""

    def test_stats_updated_for_matched(self):
        stream = _make_stream()
        stats = self._stats()
        write_line('{"msg": "hi"}', stream, stats, [], [], [], matched=True,
                   parsed={"msg": "hi"})
        assert stats.matched == 1
        assert stats.total == 1

    def test_stats_updated_for_unmatched(self):
        stream = _make_stream()
        stats = self._stats()
        write_line("skip me", stream, stats, [], [], [], matched=False, parsed=None)
        assert stats.matched == 0
        assert stats.total == 1

    def test_redact_field_applied(self):
        stream = _make_stream()
        stats = self._stats()
        parsed = {"user": "alice", "password": "secret"}
        line = json.dumps(parsed)
        write_line(line, stream, stats, [], ["password"], [], matched=True, parsed=parsed)
        output = stream.getvalue()
        assert "secret" not in output

    def test_redact_pattern_applied(self):
        stream = _make_stream()
        stats = self._stats()
        line = "user contacted support@example.com"
        write_line(line, stream, stats, [], [], ["email"], matched=True, parsed=None)
        output = stream.getvalue()
        assert "support@example.com" not in output

    def test_highlight_applied(self):
        stream = _make_stream()
        stats = self._stats()
        write_line("ERROR something bad", stream, stats, ["ERROR"], [], [],
                   matched=True, parsed=None)
        output = stream.getvalue()
        assert "ERROR" in output


class TestWriteSummary:
    def test_writes_summary_to_stream(self):
        stream = _make_stream()
        stats = LogStats()
        write_summary(stats, stream)
        assert stream.getvalue().strip() != ""


class TestRunOutput:
    def test_run_output_writes_lines(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text('{"level": "info", "msg": "started"}\n')
        stream = _make_stream()
        with patch("logdrift.output._get_output_stream", return_value=stream):
            run_output(str(log_file))
        assert "started" in stream.getvalue()

    def test_run_output_with_redact_fields(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text('{"level": "info", "token": "abc123"}\n')
        stream = _make_stream()
        with patch("logdrift.output._get_output_stream", return_value=stream):
            run_output(str(log_file), redact_fields=["token"])
        assert "abc123" not in stream.getvalue()

    def test_run_output_with_redact_patterns(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("request from 10.0.0.1 received\n")
        stream = _make_stream()
        with patch("logdrift.output._get_output_stream", return_value=stream):
            run_output(str(log_file), redact_patterns=["ipv4"])
        assert "10.0.0.1" not in stream.getvalue()

    def test_run_output_show_stats(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text('{"level": "info", "msg": "hi"}\n')
        stream = _make_stream()
        with patch("logdrift.output._get_output_stream", return_value=stream):
            run_output(str(log_file), show_stats=True)
        output = stream.getvalue()
        assert len(output.strip().splitlines()) >= 2
