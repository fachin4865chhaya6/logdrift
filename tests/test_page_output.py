"""Tests for logdrift.page_output."""
from unittest.mock import MagicMock
from logdrift.pager import Pager
from logdrift.page_output import (
    make_page_callback,
    push_to_pager,
    flush_pager,
    build_pager_from_args,
    _default_page_callback,
)


def _pager(size: int = 2) -> Pager:
    return Pager(page_size=size)


class TestMakePageCallback:
    def test_none_returns_default(self):
        cb = make_page_callback(None)
        assert cb is _default_page_callback

    def test_custom_callback_returned(self):
        custom = MagicMock()
        assert make_page_callback(custom) is custom


class TestPushToPager:
    def test_none_pager_is_noop(self):
        cb = MagicMock()
        push_to_pager(None, "line", cb)
        cb.assert_not_called()

    def test_no_callback_before_page_full(self):
        cb = MagicMock()
        p = _pager(3)
        push_to_pager(p, "a", cb)
        push_to_pager(p, "b", cb)
        cb.assert_not_called()

    def test_callback_called_when_page_full(self):
        cb = MagicMock()
        p = _pager(2)
        push_to_pager(p, "a", cb)
        push_to_pager(p, "b", cb)
        cb.assert_called_once_with(1, ["a", "b"])


class TestFlushPager:
    def test_none_pager_is_noop(self):
        cb = MagicMock()
        flush_pager(None, cb)
        cb.assert_not_called()

    def test_empty_buffer_no_callback(self):
        cb = MagicMock()
        p = _pager(5)
        flush_pager(p, cb)
        cb.assert_not_called()

    def test_partial_buffer_flushed(self):
        cb = MagicMock()
        p = _pager(5)
        push_to_pager(p, "x", cb)
        flush_pager(p, cb)
        cb.assert_called_once_with(1, ["x"])


class TestBuildPagerFromArgs:
    def test_no_page_size_attr_returns_none(self):
        args = MagicMock(spec=[])
        assert build_pager_from_args(args) is None

    def test_none_page_size_returns_none(self):
        args = MagicMock()
        args.page_size = None
        assert build_pager_from_args(args) is None

    def test_valid_page_size_returns_pager(self):
        args = MagicMock()
        args.page_size = 10
        p = build_pager_from_args(args)
        assert isinstance(p, Pager)
        assert p.page_size == 10
