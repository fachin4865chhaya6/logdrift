"""Tests for logdrift.splitter_output."""

from __future__ import annotations

import json
from typing import Optional

import pytest

from logdrift.splitter import LineSplitter
from logdrift.splitter_output import (
    _default_split_callback,
    make_split_output,
    record_for_split,
    write_split_output,
)


def _line(data: dict) -> str:
    return json.dumps(data)


# ---------------------------------------------------------------------------
# make_split_output
# ---------------------------------------------------------------------------

class TestMakeSplitOutput:
    def test_none_field_returns_none(self):
        assert make_split_output(None) is None

    def test_empty_field_returns_none(self):
        assert make_split_output("") is None

    def test_valid_field_returns_splitter(self):
        result = make_split_output("level")
        assert isinstance(result, LineSplitter)

    def test_splitter_has_correct_field(self):
        result = make_split_output("service")
        assert result.field == "service"

    def test_max_buckets_forwarded(self):
        result = make_split_output("env", max_buckets=4)
        assert result.max_buckets == 4


# ---------------------------------------------------------------------------
# record_for_split
# ---------------------------------------------------------------------------

class TestRecordForSplit:
    def test_none_splitter_returns_none(self):
        assert record_for_split(None, _line({"level": "info"})) is None

    def test_returns_bucket_key_for_json(self):
        splitter = make_split_output("level")
        key = record_for_split(splitter, _line({"level": "warn"}))
        assert key == "warn"

    def test_plain_text_returns_none(self):
        splitter = make_split_output("level")
        assert record_for_split(splitter, "not json") is None

    def test_multiple_values_create_separate_buckets(self):
        splitter = make_split_output("level")
        record_for_split(splitter, _line({"level": "info"}))
        record_for_split(splitter, _line({"level": "error"}))
        assert set(splitter.buckets().keys()) == {"info", "error"}


# ---------------------------------------------------------------------------
# write_split_output
# ---------------------------------------------------------------------------

class TestWriteSplitOutput:
    def test_none_splitter_is_noop(self):
        called = []
        write_split_output(None, callback=lambda b, ls: called.append(b))
        assert called == []

    def test_callback_called_per_bucket(self):
        splitter = make_split_output("level")
        record_for_split(splitter, _line({"level": "info"}))
        record_for_split(splitter, _line({"level": "error"}))

        seen: dict[str, list[str]] = {}
        write_split_output(splitter, callback=lambda b, ls: seen.update({b: ls}))
        assert set(seen.keys()) == {"info", "error"}

    def test_callback_receives_correct_lines(self):
        splitter = make_split_output("level")
        raw = _line({"level": "debug", "msg": "hello"})
        record_for_split(splitter, raw)

        captured: list[str] = []
        write_split_output(
            splitter,
            callback=lambda b, ls: captured.extend(ls),
        )
        assert raw in captured

    def test_default_callback_used_when_none(self, capsys):
        splitter = make_split_output("level")
        record_for_split(splitter, _line({"level": "info", "msg": "hi"}))
        write_split_output(splitter)  # uses _default_split_callback
        out = capsys.readouterr().out
        assert "info" in out
