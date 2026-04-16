"""Tests for logdrift.scorer and logdrift.score_output."""
import pytest
from logdrift.scorer import LineScorer, parse_score_weights, make_scorer, ScoredLine
from logdrift.score_output import (
    score_line, passes_score_threshold, annotate_line_with_score, make_score_threshold
)
import json


class TestParseScoreWeights:
    def test_none_returns_empty(self):
        assert parse_score_weights(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_score_weights("") == {}

    def test_single_keyword_default_weight(self):
        assert parse_score_weights("error") == {"error": 1.0}

    def test_single_keyword_with_weight(self):
        assert parse_score_weights("error:3.5") == {"error": 3.5}

    def test_multiple_keywords(self):
        result = parse_score_weights("error:2,warn,critical:5")
        assert result == {"error": 2.0, "warn": 1.0, "critical": 5.0}

    def test_invalid_weight_raises(self):
        with pytest.raises(ValueError, match="Invalid weight"):
            parse_score_weights("error:abc")

    def test_whitespace_stripped(self):
        result = parse_score_weights(" error : 2.0 , warn ")
        assert result["error"] == 2.0
        assert result["warn"] == 1.0


class TestLineScorer:
    def test_no_match_returns_zero(self):
        scorer = LineScorer(weights={"error": 2.0})
        result = scorer.score("everything is fine")
        assert result.score == 0.0
        assert result.matched_terms == []

    def test_single_match(self):
        scorer = LineScorer(weights={"error": 2.0})
        result = scorer.score("an error occurred")
        assert result.score == 2.0
        assert "error" in result.matched_terms

    def test_multiple_matches_summed(self):
        scorer = LineScorer(weights={"error": 2.0, "critical": 3.0})
        result = scorer.score("critical error detected")
        assert result.score == 5.0
        assert set(result.matched_terms) == {"error", "critical"}

    def test_case_insensitive(self):
        scorer = LineScorer(weights={"error": 1.0})
        result = scorer.score("ERROR: something failed")
        assert result.score == 1.0

    def test_make_scorer_none_returns_none(self):
        assert make_scorer(None) is None

    def test_make_scorer_returns_scorer(self):
        s = make_scorer("error:2")
        assert isinstance(s, LineScorer)


class TestScoreOutput:
    def test_score_line_none_scorer_returns_none(self):
        assert score_line(None, "some line") is None

    def test_score_line_returns_scored(self):
        scorer = LineScorer(weights={"fail": 1.0})
        result = score_line(scorer, "fail here")
        assert isinstance(result, ScoredLine)

    def test_passes_threshold_none_scored(self):
        assert passes_score_threshold(None, 5.0) is True

    def test_passes_threshold_above(self):
        scored = ScoredLine(raw="x", score=3.0, matched_terms=[])
        assert passes_score_threshold(scored, 2.0) is True

    def test_fails_threshold_below(self):
        scored = ScoredLine(raw="x", score=1.0, matched_terms=[])
        assert passes_score_threshold(scored, 2.0) is False

    def test_annotate_json_line(self):
        scored = ScoredLine(raw='{"msg":"hi"}', score=2.0, matched_terms=["hi"])
        result = annotate_line_with_score('{"msg":"hi"}', scored)
        data = json.loads(result)
        assert data["_score"] == 2.0
        assert data["_matched"] == ["hi"]

    def test_annotate_plain_text_unchanged(self):
        scored = ScoredLine(raw="plain", score=1.0, matched_terms=[])
        result = annotate_line_with_score("plain text", scored)
        assert result == "plain text"

    def test_make_score_threshold_none_returns_zero(self):
        assert make_score_threshold(None) == 0.0

    def test_make_score_threshold_value(self):
        assert make_score_threshold(3.5) == 3.5
