"""Tests for logdrift.tailer module."""

import os
import tempfile
import pytest

from logdrift.tailer import tail_file


class TestTailFile:
    """Tests for the tail_file generator."""

    def _write_lines(self, fh, lines):
        for line in lines:
            fh.write(line + "\n")
        fh.flush()

    def test_raises_if_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            list(tail_file("/nonexistent/path/to/logfile.log", follow=False))

    def test_reads_all_lines_without_follow(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            self._write_lines(fh, ['{"level": "info", "msg": "start"}',
                                   '{"level": "error", "msg": "boom"}'])
            path = fh.name
        try:
            results = list(tail_file(path, follow=False))
            assert len(results) == 2
        finally:
            os.unlink(path)

    def test_regex_filter_applied(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            self._write_lines(fh, ['{"level": "info", "msg": "hello"}',
                                   '{"level": "error", "msg": "world"}',
                                   'plain text line'])
            path = fh.name
        try:
            results = list(tail_file(path, regex_pattern=r"error", follow=False))
            assert len(results) == 1
            assert "error" in results[0]
        finally:
            os.unlink(path)

    def test_json_filter_applied(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            self._write_lines(fh, ['{"level": "info", "msg": "ok"}',
                                   '{"level": "error", "msg": "fail"}',
                                   '{"level": "warn", "msg": "meh"}'])
            path = fh.name
        try:
            results = list(tail_file(path, json_filter="level=error", follow=False))
            assert len(results) == 1
            assert "fail" in results[0]
        finally:
            os.unlink(path)

    def test_on_line_callback_called(self):
        collected = []
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            self._write_lines(fh, ['{"level": "info", "msg": "a"}',
                                   '{"level": "info", "msg": "b"}'])
            path = fh.name
        try:
            list(tail_file(path, follow=False, on_line=collected.append))
            assert len(collected) == 2
        finally:
            os.unlink(path)

    def test_empty_file_yields_nothing(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            path = fh.name
        try:
            results = list(tail_file(path, follow=False))
            assert results == []
        finally:
            os.unlink(path)

    def test_no_match_yields_nothing(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as fh:
            self._write_lines(fh, ['{"level": "info", "msg": "hello"}'])
            path = fh.name
        try:
            results = list(tail_file(path, regex_pattern=r"critical", follow=False))
            assert results == []
        finally:
            os.unlink(path)
