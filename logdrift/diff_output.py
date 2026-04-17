"""Output helpers for the line differ."""
from __future__ import annotations
from typing import Callable
from logdrift.differ import LineDiffer, parse_diff_fields


def make_line_differ(fields_arg: str | None) -> LineDiffer | None:
    fields = parse_diff_fields(fields_arg)
    if not fields:
        return None
    return LineDiffer(fields=fields)


def record_diff(
    differ: LineDiffer | None,
    line: str,
    callback: Callable[[str], None] | None = None,
) -> None:
    if differ is None:
        return
    diffs = differ.diff(line)
    if diffs is None:
        return
    formatted = differ.format_diff(diffs)
    if formatted and callback:
        callback(formatted)


def _default_diff_callback(msg: str) -> None:
    print(msg)


def write_diff_summary(differ: LineDiffer | None, stream=None) -> None:
    import sys
    out = stream or sys.stderr
    if differ is None:
        return
    out.write(
        f"[differ] total={differ.total} changed={differ.changes}\n"
    )
