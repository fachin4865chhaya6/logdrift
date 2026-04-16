"""Integration test: pager + page_output work together end-to-end."""
from logdrift.pager import Pager
from logdrift.page_output import push_to_pager, flush_pager, make_page_callback


def test_full_pipeline_collects_all_lines():
    collected: list = []

    def cb(page_number, lines):
        collected.extend(lines)

    p = Pager(page_size=3)
    callback = make_page_callback(cb)
    all_lines = [f"line-{i}" for i in range(7)]
    for line in all_lines:
        push_to_pager(p, line, callback)
    flush_pager(p, callback)

    assert collected == all_lines


def test_page_numbers_are_sequential():
    pages: list = []

    def cb(page_number, lines):
        pages.append((page_number, lines))

    p = Pager(page_size=2)
    for line in ["a", "b", "c", "d"]:
        push_to_pager(p, line, cb)
    flush_pager(p, cb)

    assert [pn for pn, _ in pages] == [1, 2]


def test_single_line_flushed_as_page_one():
    pages: list = []

    def cb(page_number, lines):
        pages.append((page_number, lines))

    p = Pager(page_size=10)
    push_to_pager(p, "only", cb)
    flush_pager(p, cb)

    assert pages == [(1, ["only"])]
