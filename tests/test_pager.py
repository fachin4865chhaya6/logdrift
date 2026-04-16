"""Tests for logdrift.pager."""
import pytest
from logdrift.pager import Pager, parse_page_size, make_pager


class TestPager:
    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError):
            Pager(page_size=0)

    def test_negative_page_size_raises(self):
        with pytest.raises(ValueError):
            Pager(page_size=-1)

    def test_push_below_limit_returns_none(self):
        p = Pager(page_size=3)
        assert p.push("a") is None
        assert p.push("b") is None

    def test_push_at_limit_returns_page(self):
        p = Pager(page_size=2)
        p.push("a")
        result = p.push("b")
        assert result == ["a", "b"]

    def test_page_number_increments_on_flush(self):
        p = Pager(page_size=2)
        p.push("a")
        p.push("b")
        assert p.page_number == 1

    def test_buffer_cleared_after_flush(self):
        p = Pager(page_size=2)
        p.push("a")
        p.push("b")
        assert p.buffered == 0

    def test_flush_remaining_returns_partial_page(self):
        p = Pager(page_size=5)
        p.push("x")
        result = p.flush_remaining()
        assert result == ["x"]

    def test_flush_remaining_empty_returns_none(self):
        p = Pager(page_size=5)
        assert p.flush_remaining() is None

    def test_multiple_pages(self):
        p = Pager(page_size=2)
        pages = []
        for line in ["a", "b", "c", "d", "e"]:
            result = p.push(line)
            if result:
                pages.append(result)
        remainder = p.flush_remaining()
        if remainder:
            pages.append(remainder)
        assert pages == [["a", "b"], ["c", "d"], ["e"]]
        assert p.page_number == 3


class TestParsePageSize:
    def test_none_returns_none(self):
        assert parse_page_size(None) is None

    def test_valid_string_returns_int(self):
        assert parse_page_size("10") == 10

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_page_size("abc")

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            parse_page_size("0")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            parse_page_size("-5")


class TestMakePager:
    def test_none_returns_none(self):
        assert make_pager(None) is None

    def test_returns_pager_instance(self):
        p = make_pager(20)
        assert isinstance(p, Pager)
        assert p.page_size == 20
