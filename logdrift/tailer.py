"""Log file tailer with filtering support."""

import time
import os
from typing import Optional, Callable, Iterator

from logdrift.parser import filter_line


DEFAULT_POLL_INTERVAL = 0.1


def tail_file(
    filepath: str,
    regex_pattern: Optional[str] = None,
    json_filter: Optional[str] = None,
    follow: bool = True,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    on_line: Optional[Callable[[str], None]] = None,
) -> Iterator[str]:
    """Tail a file, yielding lines that match the given filters.

    Args:
        filepath: Path to the log file to tail.
        regex_pattern: Optional regex pattern to filter lines.
        json_filter: Optional JSON path filter in the form 'key.subkey=value'.
        follow: If True, keep watching the file for new lines (like tail -f).
        poll_interval: Seconds to wait between polling for new content.
        on_line: Optional callback invoked for each matched line.

    Yields:
        Matched log lines as strings.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Log file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        # Seek to end when following, read from beginning otherwise
        if follow:
            fh.seek(0, os.SEEK_END)

        while True:
            line = fh.readline()

            if not line:
                if not follow:
                    break
                time.sleep(poll_interval)
                # Re-check if file was rotated
                try:
                    current_inode = os.stat(filepath).st_ino
                    fd_inode = os.fstat(fh.fileno()).st_ino
                    if current_inode != fd_inode:
                        fh.close()
                        fh = open(filepath, "r", encoding="utf-8", errors="replace")
                except OSError:
                    pass
                continue

            stripped = line.rstrip("\n")
            if filter_line(stripped, regex_pattern=regex_pattern, json_filter=json_filter):
                if on_line is not None:
                    on_line(stripped)
                yield stripped
