"""Handles log file rotation detection for the tailer."""

import os
from typing import Optional


class RotationDetector:
    """Detects if a log file has been rotated by tracking inode and size."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self._inode: Optional[int] = None
        self._size: int = 0
        self._refresh()

    def _refresh(self) -> None:
        """Update stored inode and size from current file stat."""
        try:
            stat = os.stat(self.filepath)
            self._inode = stat.st_ino
            self._size = stat.st_size
        except FileNotFoundError:
            self._inode = None
            self._size = 0

    def has_rotated(self) -> bool:
        """Return True if the file has been rotated or truncated since last check."""
        try:
            stat = os.stat(self.filepath)
        except FileNotFoundError:
            return False

        rotated = (
            stat.st_ino != self._inode
            or stat.st_size < self._size
        )
        return rotated

    def reset(self) -> None:
        """Reset detector state to current file, e.g. after reopening."""
        self._refresh()

    @property
    def inode(self) -> Optional[int]:
        return self._inode

    @property
    def size(self) -> int:
        return self._size


def make_rotation_detector(filepath: str) -> RotationDetector:
    """Factory function to create a RotationDetector for a given file path."""
    return RotationDetector(filepath)
