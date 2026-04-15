"""Statistics tracking for log tailing sessions."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LogStats:
    total_lines: int = 0
    matched_lines: int = 0
    skipped_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    error_count: int = 0

    def record_line(self, matched: bool, level: Optional[str] = None) -> None:
        """Record a processed log line."""
        self.total_lines += 1
        if matched:
            self.matched_lines += 1
            if level:
                normalized = level.upper()
                self.level_counts[normalized] += 1
                if normalized in ("ERROR", "CRITICAL", "FATAL"):
                    self.error_count += 1
        else:
            self.skipped_lines += 1

    def match_rate(self) -> float:
        """Return the ratio of matched to total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.matched_lines / self.total_lines

    def summary(self) -> Dict:
        """Return a dict summary of collected stats."""
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "skipped_lines": self.skipped_lines,
            "match_rate": round(self.match_rate(), 4),
            "error_count": self.error_count,
            "level_counts": dict(self.level_counts),
        }

    def format_summary(self) -> str:
        """Return a human-readable summary string."""
        s = self.summary()
        lines = [
            "--- logdrift session stats ---",
            f"  Total lines   : {s['total_lines']}",
            f"  Matched lines : {s['matched_lines']}",
            f"  Skipped lines : {s['skipped_lines']}",
            f"  Match rate    : {s['match_rate'] * 100:.1f}%",
            f"  Errors        : {s['error_count']}",
        ]
        if s["level_counts"]:
            lines.append("  Level counts  :")
            for lvl, cnt in sorted(s["level_counts"].items()):
                lines.append(f"    {lvl:<10}: {cnt}")
        lines.append("------------------------------")
        return "\n".join(lines)
