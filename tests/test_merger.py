"""Tests for logdrift.merger and logdrift.merge_output."""
import json
import pytest

from logdrift.merger import LineMerger, parse_merge_fields
from logdrift.merge_output import make_line_merger, record_for_merging, write_merge_summary


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestParseMergeFields:
    def test_none_returns_empty(self):
        assert parse_merge_fields(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_merge_fields("") == []

    def test_single_field(self):
        assert parse_merge_fields("user") == ["user"]

    def test_multiple_fields(self):
        assert parse_merge_fields("user,status,code") == ["user", "status", "code"]

    def test_strips_whitespace(self):
        assert parse_merge_fields(" a , b ") == ["a", "b"]


class TestLineMerger:
    def test_empty_key_field_raises(self):
        with pytest.raises(ValueError):
            LineMerger(key_field="", merge_fields=["f"])

    def test_empty_merge_fields_raises(self):
        with pytest.raises(ValueError):
            LineMerger(key_field="id", merge_fields=[])

    def test_max_keys_zero_raises(self):
        with pytest.raises(ValueError):
            LineMerger(key_field="id", merge_fields=["f"], max_keys=0)

    def test_add_plain_text_returns_none(self):
        m = LineMerger(key_field="id", merge_fields=["status"])
        assert m.add("not json") is None

    def test_add_missing_key_returns_none(self):
        m = LineMerger(key_field="id", merge_fields=["status"])
        assert m.add(_line(status="ok")) is None

    def test_add_returns_key(self):
        m = LineMerger(key_field="id", merge_fields=["status"])
        assert m.add(_line(id="abc", status="ok")) == "abc"

    def test_merged_fields_stored(self):
        m = LineMerger(key_field="id", merge_fields=["status", "code"])
        m.add(_line(id="x", status="ok", code=200))
        assert m.get_merged("x") == {"status": "ok", "code": 200}

    def test_fields_updated_across_lines(self):
        m = LineMerger(key_field="id", merge_fields=["status"])
        m.add(_line(id="x", status="ok"))
        m.add(_line(id="x", status="error"))
        assert m.get_merged("x") == {"status": "error"}

    def test_max_keys_evicts_oldest(self):
        m = LineMerger(key_field="id", merge_fields=["v"], max_keys=2)
        m.add(_line(id="a", v=1))
        m.add(_line(id="b", v=2))
        m.add(_line(id="c", v=3))
        assert m.get_merged("a") is None
        assert m.get_merged("c") == {"v": 3}

    def test_format_summary_contains_keys(self):
        m = LineMerger(key_field="id", merge_fields=["v"])
        m.add(_line(id="z", v=99))
        summary = m.format_summary()
        assert "z" in summary


class TestMakeLineMerger:
    def test_none_key_returns_none(self):
        assert make_line_merger(None, "f") is None

    def test_empty_key_returns_none(self):
        assert make_line_merger("", "f") is None

    def test_empty_fields_returns_none(self):
        assert make_line_merger("id", "") is None

    def test_valid_returns_merger(self):
        m = make_line_merger("id", "status,code")
        assert isinstance(m, LineMerger)
        assert m.key_field == "id"
        assert m.merge_fields == ["status", "code"]


class TestWriteMergeSummary:
    def test_none_merger_is_noop(self):
        write_merge_summary(None)  # should not raise

    def test_callback_called_for_each_key(self):
        m = make_line_merger("id", "v")
        m.add(_line(id="a", v=1))
        m.add(_line(id="b", v=2))
        collected = {}
        write_merge_summary(m, callback=lambda k, d: collected.update({k: d}))
        assert collected == {"a": {"v": 1}, "b": {"v": 2}}
