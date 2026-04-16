"""Score output helpers: filter or annotate lines by score threshold."""
from __future__ import annotations
from typing import Optional

from logdrift.scorer import LineScorer, ScoredLine, make_scorer
from logdrift.parser import parse_line
import json


def score_line(scorer: Optional[LineScorer], line: str) -> Optional[ScoredLine]:
    if scorer is None:
        return None
    return scorer.score(line)


def passes_score_threshold(scored: Optional[ScoredLine], threshold: float) -> bool:
    if scored is None:
        return True
    return scored.score >= threshold


def annotate_line_with_score(line: str, scored: Optional[ScoredLine]) -> str:
    """If line is JSON and scored, inject _score and _matched fields."""
    if scored is None:
        return line
    data = parse_line(line)
    if data is None:
        return line
    data["_score"] = scored.score
    data["_matched"] = scored.matched_terms
    return json.dumps(data)


def make_score_threshold(value: Optional[float]) -> float:
    return value if value is not None else 0.0
