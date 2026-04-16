"""Line scorer: assigns a numeric relevance score to log lines based on keyword weights."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re

from logdrift.parser import parse_line


@dataclass
class ScoredLine:
    raw: str
    score: float
    matched_terms: list[str]


@dataclass
class LineScorer:
    weights: dict[str, float] = field(default_factory=dict)

    def score(self, line: str) -> ScoredLine:
        total = 0.0
        matched: list[str] = []
        lower = line.lower()
        for term, weight in self.weights.items():
            if term.lower() in lower:
                total += weight
                matched.append(term)
        return ScoredLine(raw=line, score=total, matched_terms=matched)


def parse_score_weights(spec: Optional[str]) -> dict[str, float]:
    """Parse 'keyword:weight,...' into a dict. Weight defaults to 1.0."""
    if not spec:
        return {}
    result: dict[str, float] = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            term, _, raw_weight = part.partition(":")
            try:
                result[term.strip()] = float(raw_weight.strip())
            except ValueError:
                raise ValueError(f"Invalid weight for term '{term.strip()}': '{raw_weight.strip()}'")
        else:
            result[part] = 1.0
    return result


def make_scorer(spec: Optional[str]) -> Optional[LineScorer]:
    weights = parse_score_weights(spec)
    if not weights:
        return None
    return LineScorer(weights=weights)
