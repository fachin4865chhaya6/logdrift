"""Output helpers for the line merger feature."""
from __future__ import annotations

from typing import Callable, Optional

from logdrift.merger import LineMerger, parse_merge_fields


def make_line_merger(
    key_field: Optional[str],
    merge_fields_spec: Optional[str],
    max_keys: int = 1000,
) -> Optional[LineMerger]:
    """Create a LineMerger from config values, or return None if misconfigured.

    Args:
        key_field: The field name to group lines by.
        merge_fields_spec: Comma-separated field names to merge/accumulate.
        max_keys: Maximum number of distinct keys to track in memory.

    Returns:
        A configured LineMerger, or None if key_field or merge_fields are absent.
    """
    if not key_field or not key_field.strip():
        return None
    fields = parse_merge_fields(merge_fields_spec)
    if not fields:
        return None
    return LineMerger(key_field=key_field.strip(), merge_fields=fields, max_keys=max_keys)


def record_for_merging(merger: Optional[LineMerger], line: str) -> Optional[str]:
    """Feed a log line to the merger if one is active.

    Returns the evicted key if the merger's key limit was reached, else None.
    """
    if merger is None:
        return None
    return merger.add(line)


def _default_merge_callback(key: str, merged: dict) -> None:
    print(f"[merge] {key} -> {merged}")


def write_merge_summary(
    merger: Optional[LineMerger],
    callback: Optional[Callable[[str, dict], None]] = None,
) -> None:
    """Emit all accumulated merge data via callback.

    Args:
        merger: The LineMerger instance to summarise, or None (no-op).
        callback: Called with (key, merged_dict) for each tracked key.
                  Defaults to printing to stdout.
    """
    if merger is None:
        return
    cb = callback or _default_merge_callback
    for key in merger.keys():
        data = merger.get_merged(key)
        if data is not None:
            cb(key, data)
