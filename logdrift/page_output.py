"""Page output helpers — integrates Pager into the logdrift output pipeline."""
from __future__ import annotations

from typing import Callable, List, Optional

from logdrift.pager import Pager, make_pager, parse_page_size

PageCallback = Callable[[int, List[str]], None]


def _default_page_callback(page_number: int, lines: List[str]) -> None:
    header = f"--- Page {page_number} ---"
    print(header)
    for line in lines:
        print(line)


def make_page_callback(cb: Optional[PageCallback] = None) -> PageCallback:
    return cb if cb is not None else _default_page_callback


def push_to_pager(
    pager: Optional[Pager],
    line: str,
    callback: PageCallback,
) -> None:
    if pager is None:
        return
    page = pager.push(line)
    if page is not None:
        callback(pager.page_number, page)


def flush_pager(
    pager: Optional[Pager],
    callback: PageCallback,
) -> None:
    if pager is None:
        return
    page = pager.flush_remaining()
    if page is not None:
        callback(pager.page_number, page)


def build_pager_from_args(args: object) -> Optional[Pager]:
    raw = getattr(args, "page_size", None)
    size = parse_page_size(str(raw) if raw is not None else None)
    return make_pager(size)
