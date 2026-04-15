"""File tailing logic for logdrift."""

import time
from typing import Callable, Iterator, List, Optional

from logdrift.parser import filter_line
from logdrift.stats import LogStats


def tail_file(
    filepath: str,
    follow: bool = False,
    regex_filter: Optional[str] = None,
    json_filter: Optional[dict] = None,
    stats: Optional[LogStats] = None,
) -> Iterator[str]:
    """Tail a file, yielding lines that pass the active filters.

    Args:
        filepath: Path to the log file to read.
        follow: If True, keep watching for new lines after EOF.
        regex_filter: Optional regex pattern to match against each line.
        json_filter: Optional dict of JSON path -> expected value filters.
        stats: Optional LogStats instance to record match/skip counts.

    Yields:
        Lines that pass all active filters.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    try:
        fh = open(filepath, "r", encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Log file not found: {filepath}")

    try:
        while True:
            line = fh.readline()
            if not line:
                if follow:
                    time.sleep(0.1)
                    continue
                break

            line = line.rstrip("\n")
            passed, level = filter_line(
                line,
                regex_filter=regex_filter,
                json_filter=json_filter,
            )

            if stats is not None:
                stats.record_line(matched=passed, level=level)

            if passed:
                yield line
    finally:
        fh.close()
