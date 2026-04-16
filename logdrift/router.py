"""Route log lines to different output files based on field value or regex."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, IO, List, Optional

from logdrift.parser import parse_line, get_json_path_value


@dataclass
class RouteRule:
    pattern: str
    destination: str
    field_path: Optional[str] = None
    _regex: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.pattern:
            raise ValueError("pattern must not be empty")
        if not self.destination:
            raise ValueError("destination must not be empty")
        self._regex = re.compile(self.pattern)

    def matches(self, line: str) -> bool:
        parsed = parse_line(line)
        if parsed is not None and self.field_path:
            value = get_json_path_value(parsed, self.field_path)
            target = str(value) if value is not None else ""
        else:
            target = line
        return bool(self._regex.search(target))


def parse_route_rules(spec: Optional[str]) -> List[RouteRule]:
    """Parse rules from 'pattern:destination' comma-separated string."""
    if not spec:
        return []
    rules = []
    for part in spec.split(","):
        part = part.strip()
        if ":" not in part:
            raise ValueError(f"Invalid route rule (missing ':'): {part!r}")
        pattern, _, destination = part.partition(":")
        rules.append(RouteRule(pattern=pattern.strip(), destination=destination.strip()))
    return rules


class LineRouter:
    def __init__(self, rules: List[RouteRule]) -> None:
        self._rules = rules
        self._streams: Dict[str, IO[str]] = {}

    def _get_stream(self, destination: str) -> IO[str]:
        if destination not in self._streams:
            self._streams[destination] = open(destination, "a", encoding="utf-8")  # noqa: SIM115
        return self._streams[destination]

    def route(self, line: str) -> Optional[str]:
        """Write line to first matching destination. Returns destination or None."""
        for rule in self._rules:
            if rule.matches(line):
                stream = self._get_stream(rule.destination)
                stream.write(line if line.endswith("\n") else line + "\n")
                stream.flush()
                return rule.destination
        return None

    def close(self) -> None:
        for stream in self._streams.values():
            stream.close()
        self._streams.clear()
