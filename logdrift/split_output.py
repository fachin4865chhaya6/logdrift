"""Integration helpers: wire LineSplitter into the logdrift output pipeline."""

from __future__ import annotations

import sys
from typing import Callable, List, Optional

from logdrift.splitter import LineSplitter, make_splitter, write_split_summary


def make_split_output(field: Optional[str]) -> Optional[LineSplitter]:
    """Create a LineSplitter from a CLI field argument, or return None."""
    return make_splitter(field)


def record_for_split(splitter: Optional[LineSplitter], line: str) -> Optional[str]:
    """Feed a line into the splitter if one is active. Returns bucket key or None."""
    if splitter is None:
        return None
    return splitter.add(line)


def _default_split_callback(
    field: str,
    key: str,
    lines: List[str],
    stream=None,
) -> None:
    out = stream or sys.stdout
    out.write(f"[split:{field}={key}] {len(lines)} line(s)\n")
    for line in lines:
        out.write(f"  {line.rstrip()}\n")


def write_split_output(
    splitter: Optional[LineSplitter],
    callback: Optional[Callable[[str, str, List[str]], None]] = None,
    stream=None,
) -> None:
    """Write the split summary using *callback*, defaulting to stdout output."""
    if splitter is None:
        return
    if callback is None:
        def callback(field: str, key: str, lines: List[str]) -> None:
            _default_split_callback(field, key, lines, stream=stream)
    write_split_summary(splitter, callback)
