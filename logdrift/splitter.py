"""Field-based log line splitter: splits a stream of lines into named buckets."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Optional

from logdrift.parser import parse_line, get_json_path_value


def parse_split_field(value: Optional[str]) -> str:
    """Validate and return the field name to split on."""
    if not value or not value.strip():
        raise ValueError("split_field must be a non-empty string")
    return value.strip()


class LineSplitter:
    """Accumulates log lines into buckets keyed by a JSON field value."""

    def __init__(self, field: str) -> None:
        if not field or not field.strip():
            raise ValueError("field must be a non-empty string")
        self._field = field.strip()
        self._buckets: Dict[str, List[str]] = defaultdict(list)
        self._unmatched: List[str] = []

    @property
    def field(self) -> str:
        return self._field

    @property
    def buckets(self) -> Dict[str, List[str]]:
        return dict(self._buckets)

    @property
    def unmatched(self) -> List[str]:
        return list(self._unmatched)

    def add(self, line: str) -> Optional[str]:
        """Add a line to the appropriate bucket. Returns the bucket key or None."""
        data = parse_line(line)
        if data is None:
            self._unmatched.append(line)
            return None
        value = get_json_path_value(data, self._field)
        if value is None:
            self._unmatched.append(line)
            return None
        key = str(value)
        self._buckets[key].append(line)
        return key

    def reset(self) -> None:
        """Clear all buckets and unmatched lines."""
        self._buckets.clear()
        self._unmatched.clear()


def make_splitter(field: Optional[str]) -> Optional[LineSplitter]:
    """Return a LineSplitter if field is provided, else None."""
    if not field or not field.strip():
        return None
    return LineSplitter(parse_split_field(field))


def write_split_summary(
    splitter: LineSplitter,
    callback: Callable[[str, str, List[str]], None],
) -> None:
    """Invoke callback(field, bucket_key, lines) for each bucket."""
    for key, lines in splitter.buckets.items():
        callback(splitter.field, key, lines)
