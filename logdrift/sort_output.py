from __future__ import annotations
from typing import Optional, Callable
from logdrift.sorter import LineSorter, parse_sort_field, parse_sort_limit


def make_line_sorter(
    sort_field: Optional[str],
    limit: Optional[str] = None,
    reverse: bool = False,
) -> Optional[LineSorter]:
    field = parse_sort_field(sort_field)
    if field is None:
        return None
    n = parse_sort_limit(limit)
    return LineSorter(sort_field=field, limit=n, reverse=reverse)


def record_for_sorting(sorter: Optional[LineSorter], raw: str) -> None:
    if sorter is None:
        return
    sorter.add(raw)


def _default_sort_callback(lines: list) -> None:
    for line in lines:
        print(line)


def write_sort_output(
    sorter: Optional[LineSorter],
    callback: Optional[Callable[[list], None]] = None,
) -> None:
    if sorter is None:
        return
    cb = callback or _default_sort_callback
    cb(sorter.sorted_lines())
