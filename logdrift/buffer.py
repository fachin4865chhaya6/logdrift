"""Line buffer with max-size and flush-on-match support for logdrift."""

from collections import deque
from typing import Deque, Iterator, List, Optional


class LineBuffer:
    """Stores a rolling window of recent lines and emits context around matches."""

    def __init__(self, before: int = 0, after: int = 0) -> None:
        if before < 0 or after < 0:
            raise ValueError("before and after must be non-negative integers")
        self.before = before
        self.after = after
        self._pre: Deque[str] = deque(maxlen=before if before > 0 else 1)
        self._pending: List[str] = []   # lines waiting for trailing context
        self._after_remaining: int = 0  # how many 'after' lines still to emit

    def push(self, line: str, matched: bool) -> Iterator[str]:
        """Feed a line; yield lines that should be output given context rules."""
        if matched:
            # Emit pre-context lines not already emitted
            if self.before > 0:
                for pre_line in self._pre:
                    yield pre_line
            yield line
            self._after_remaining = self.after
        elif self._after_remaining > 0:
            yield line
            self._after_remaining -= 1
        # Always keep this line in the pre-context window
        if self.before > 0:
            self._pre.append(line)

    def reset(self) -> None:
        """Clear internal state."""
        self._pre.clear()
        self._pending.clear()
        self._after_remaining = 0


def parse_context_args(before: Optional[int], after: Optional[int]) -> LineBuffer:
    """Build a LineBuffer from CLI-style before/after counts."""
    b = before if before is not None else 0
    a = after if after is not None else 0
    return LineBuffer(before=b, after=a)
