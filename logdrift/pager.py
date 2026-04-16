"""Pagination support for logdrift output — buffers lines and emits pages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pager:
    page_size: int
    _buffer: List[str] = field(default_factory=list, init=False)
    _page_number: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.page_size < 1:
            raise ValueError(f"page_size must be >= 1, got {self.page_size}")

    @property
    def page_number(self) -> int:
        return self._page_number

    @property
    def buffered(self) -> int:
        return len(self._buffer)

    def push(self, line: str) -> Optional[List[str]]:
        """Add a line. Returns a full page when the buffer is flushed, else None."""
        self._buffer.append(line)
        if len(self._buffer) >= self.page_size:
            return self._flush()
        return None

    def flush_remaining(self) -> Optional[List[str]]:
        """Flush any remaining lines as a partial page."""
        if self._buffer:
            return self._flush()
        return None

    def _flush(self) -> List[str]:
        page = list(self._buffer)
        self._buffer.clear()
        self._page_number += 1
        return page


def parse_page_size(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        n = int(value)
    except ValueError:
        raise ValueError(f"Invalid page size: {value!r}")
    if n < 1:
        raise ValueError(f"Page size must be >= 1, got {n}")
    return n


def make_pager(page_size: Optional[int]) -> Optional[Pager]:
    if page_size is None:
        return None
    return Pager(page_size=page_size)
