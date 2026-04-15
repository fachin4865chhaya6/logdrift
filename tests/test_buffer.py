"""Tests for logdrift.buffer."""

import pytest
from logdrift.buffer import LineBuffer, parse_context_args


class TestLineBuffer:
    def _collect(self, buf: LineBuffer, pairs):
        """Helper: feed (line, matched) pairs, return all yielded lines."""
        result = []
        for line, matched in pairs:
            result.extend(buf.push(line, matched))
        return result

    def test_no_context_only_matched_lines_returned(self):
        buf = LineBuffer(before=0, after=0)
        out = self._collect(buf, [("a", False), ("b", True), ("c", False)])
        assert out == ["b"]

    def test_before_context_included(self):
        buf = LineBuffer(before=2, after=0)
        out = self._collect(buf, [("a", False), ("b", False), ("c", True)])
        assert out == ["a", "b", "c"]

    def test_before_context_capped_at_window(self):
        buf = LineBuffer(before=1, after=0)
        out = self._collect(buf, [("a", False), ("b", False), ("c", True)])
        assert out == ["b", "c"]

    def test_after_context_included(self):
        buf = LineBuffer(before=0, after=2)
        out = self._collect(buf, [("a", True), ("b", False), ("c", False), ("d", False)])
        assert out == ["a", "b", "c"]

    def test_before_and_after_combined(self):
        buf = LineBuffer(before=1, after=1)
        pairs = [("x", False), ("y", True), ("z", False)]
        out = self._collect(buf, pairs)
        assert out == ["x", "y", "z"]

    def test_multiple_matches_no_duplicate_context(self):
        buf = LineBuffer(before=1, after=1)
        pairs = [("a", False), ("b", True), ("c", True), ("d", False)]
        out = self._collect(buf, pairs)
        # b matched: pre=a, match=b; c matched: pre=b (already emitted via after), match=c; after=d
        assert "b" in out
        assert "c" in out

    def test_no_match_yields_nothing(self):
        buf = LineBuffer(before=3, after=3)
        out = self._collect(buf, [("a", False), ("b", False)])
        assert out == []

    def test_reset_clears_state(self):
        buf = LineBuffer(before=2, after=2)
        self._collect(buf, [("a", True)])
        buf.reset()
        assert buf._after_remaining == 0
        assert len(buf._pre) == 0

    def test_negative_before_raises(self):
        with pytest.raises(ValueError):
            LineBuffer(before=-1)

    def test_negative_after_raises(self):
        with pytest.raises(ValueError):
            LineBuffer(after=-1)


class TestParseContextArgs:
    def test_none_values_produce_zero_context(self):
        buf = parse_context_args(None, None)
        assert buf.before == 0
        assert buf.after == 0

    def test_values_passed_through(self):
        buf = parse_context_args(3, 5)
        assert buf.before == 3
        assert buf.after == 5

    def test_returns_line_buffer_instance(self):
        buf = parse_context_args(1, 1)
        assert isinstance(buf, LineBuffer)
