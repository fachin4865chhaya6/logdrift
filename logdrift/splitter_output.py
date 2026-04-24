"""Output helpers for field-based line splitting into named buckets."""

from __future__ import annotations

from typing import Callable, Optional

from logdrift.splitter import LineSplitter, parse_split_field


def make_split_output(
    field: Optional[str],
    *,
    max_buckets: int = 64,
) -> Optional[LineSplitter]:
    """Return a LineSplitter for *field*, or None if field is falsy."""
    if not field:
        return None
    f = parse_split_field(field)
    return LineSplitter(field=f, max_buckets=max_buckets)


def record_for_split(
    splitter: Optional[LineSplitter],
    raw: str,
) -> Optional[str]:
    """Add *raw* to *splitter* and return the bucket key, or None."""
    if splitter is None:
        return None
    return splitter.add(raw)


def _default_split_callback(bucket: str, lines: list[str]) -> None:
    """Print bucket header followed by its lines."""
    print(f"--- bucket: {bucket} ({len(lines)} line(s)) ---")
    for line in lines:
        print(line)


def write_split_output(
    splitter: Optional[LineSplitter],
    callback: Optional[Callable[[str, list[str]], None]] = None,
) -> None:
    """Invoke *callback* for every bucket collected by *splitter*."""
    if splitter is None:
        return
    cb = callback if callback is not None else _default_split_callback
    for bucket, lines in splitter.buckets().items():
        cb(bucket, lines)
