import json
import pytest
from logdrift.group_output import (
    make_line_grouper,
    record_for_grouping,
    write_group_summary,
)


def _line(data: dict) -> str:
    return json.dumps(data)


def test_make_line_grouper_none_returns_none():
    assert make_line_grouper(None) is None


def test_make_line_grouper_returns_grouper():
    g = make_line_grouper("level")
    assert g is not None
    assert g.group_field == "level"


def test_make_line_grouper_passes_max_groups():
    g = make_line_grouper("level", max_groups=10)
    assert g.max_groups == 10


def test_record_for_grouping_none_grouper_is_noop():
    result = record_for_grouping(None, _line({"level": "info"}))
    assert result is None


def test_record_for_grouping_returns_key():
    g = make_line_grouper("level")
    key = record_for_grouping(g, _line({"level": "warn"}))
    assert key == "warn"


def test_record_for_grouping_plain_text_returns_none():
    g = make_line_grouper("level")
    assert record_for_grouping(g, "plain text") is None


def test_write_group_summary_none_grouper_is_noop():
    called = []
    write_group_summary(None, callback=lambda s: called.append(s))
    assert called == []


def test_write_group_summary_calls_callback():
    g = make_line_grouper("level")
    record_for_grouping(g, _line({"level": "info"}))
    collected = []
    write_group_summary(g, callback=lambda s: collected.append(s))
    assert len(collected) == 1
    assert "info" in collected[0]


def test_write_group_summary_uses_default_callback(capsys):
    g = make_line_grouper("level")
    record_for_grouping(g, _line({"level": "debug"}))
    write_group_summary(g)
    captured = capsys.readouterr()
    assert "debug" in captured.out
