from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from logdrift.parser import parse_line, get_json_path_value


@dataclass
class LineGrouper:
    group_field: str
    max_groups: int = 100
    _buckets: Dict[str, List[str]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if not self.group_field.strip():
            raise ValueError("group_field must not be empty")
        if self.max_groups <= 0:
            raise ValueError("max_groups must be positive")

    @property
    def groups(self) -> Dict[str, List[str]]:
        return dict(self._buckets)

    def add(self, line: str) -> Optional[str]:
        parsed = parse_line(line)
        if parsed is None:
            return None
        key = get_json_path_value(parsed, self.group_field)
        if key is None:
            return None
        key = str(key)
        if key not in self._buckets:
            if len(self._buckets) >= self.max_groups:
                return None
            self._buckets[key] = []
        self._buckets[key].append(line)
        return key

    def get_group(self, key: str) -> List[str]:
        return list(self._buckets.get(key, []))

    def format_summary(self) -> str:
        lines = ["=== Line Groups ==="]
        for key, entries in sorted(self._buckets.items()):
            lines.append(f"  {key}: {len(entries)} line(s)")
        return "\n".join(lines)


def parse_group_field(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    return value.strip()


def make_grouper(group_field: Optional[str], max_groups: int = 100) -> Optional[LineGrouper]:
    field_name = parse_group_field(group_field)
    if field_name is None:
        return None
    return LineGrouper(group_field=field_name, max_groups=max_groups)
