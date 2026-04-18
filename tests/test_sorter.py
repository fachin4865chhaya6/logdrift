import json
import pytest
from logdrift.sorter import LineSorter, parse_sort_field, parse_sort_limit
from logdrift.sort_output import make_line_sorter, record_for_sorting, write_sort_output


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestParseSortField:
    def test_none_returns_none(self):
        assert parse_sort_field(None) is None

    def test_empty_returns_none(self):
        assert parse_sort_field("") is None

    def test_whitespace_returns_none(self):
        assert parse_sort_field("   ") is None

    def test_valid_field_returned(self):
        assert parse_sort_field("level") == "level"

    def test_strips_whitespace(self):
        assert parse_sort_field("  ts  ") == "ts"


class TestParseSortLimit:
    def test_none_returns_zero(self):
        assert parse_sort_limit(None) == 0

    def test_valid_string(self):
        assert parse_sort_limit("5") == 5

    def test_zero_allowed(self):
        assert parse_sort_limit("0") == 0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            parse_sort_limit("-1")


class TestLineSorter:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            LineSorter(sort_field="")

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError):
            LineSorter(sort_field="level", limit=-1)

    def test_add_plain_text_returns_none(self):
        s = LineSorter(sort_field="level")
        s.add("plain text")
        assert s.total == 0

    def test_add_missing_field_ignored(self):
        s = LineSorter(sort_field="missing")
        s.add(_line(level="info"))
        assert s.total == 0

    def test_sorted_ascending(self):
        s = LineSorter(sort_field="code")
        s.add(_line(code=3))
        s.add(_line(code=1))
        s.add(_line(code=2))
        result = s.sorted_lines()
        codes = [json.loads(r)["code"] for r in result]
        assert codes == [1, 2, 3]

    def test_sorted_descending(self):
        s = LineSorter(sort_field="code", reverse=True)
        s.add(_line(code=1))
        s.add(_line(code=3))
        s.add(_line(code=2))
        codes = [json.loads(r)["code"] for r in s.sorted_lines()]
        assert codes == [3, 2, 1]

    def test_limit_applied(self):
        s = LineSorter(sort_field="n", limit=2)
        for i in range(5):
            s.add(_line(n=i))
        assert len(s.sorted_lines()) == 2

    def test_format_summary_empty(self):
        s = LineSorter(sort_field="x")
        assert "no sortable" in s.format_summary()

    def test_format_summary_returns_lines(self):
        s = LineSorter(sort_field="v")
        s.add(_line(v="b"))
        s.add(_line(v="a"))
        summary = s.format_summary()
        assert summary.count("\n") == 1


def test_make_line_sorter_none_returns_none():
    assert make_line_sorter(None) is None


def test_make_line_sorter_returns_sorter():
    s = make_line_sorter("level")
    assert isinstance(s, LineSorter)


def test_record_for_sorting_none_is_noop():
    record_for_sorting(None, _line(level="info"))  # no error


def test_write_sort_output_none_is_noop():
    write_sort_output(None)  # no error


def test_write_sort_output_calls_callback():
    s = make_line_sorter("n")
    s.add(_line(n=2))
    s.add(_line(n=1))
    collected = []
    write_sort_output(s, callback=lambda lines: collected.extend(lines))
    assert len(collected) == 2
    assert json.loads(collected[0])["n"] == 1
