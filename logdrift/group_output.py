from __future__ import annotations
from typing import Optional, Callable
from logdrift.grouper import LineGrouper, make_grouper


def make_line_grouper(
    group_field: Optional[str],
    max_groups: int = 100,
) -> Optional[LineGrouper]:
    return make_grouper(group_field, max_groups=max_groups)


def record_for_grouping(grouper: Optional[LineGrouper], line: str) -> Optional[str]:
    if grouper is None:
        return None
    return grouper.add(line)


def _default_group_callback(summary: str) -> None:
    print(summary)


def write_group_summary(
    grouper: Optional[LineGrouper],
    callback: Optional[Callable[[str], None]] = None,
) -> None:
    if grouper is None:
        return
    cb = callback or _default_group_callback
    cb(grouper.format_summary())
