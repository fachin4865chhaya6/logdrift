"""Tests for logdrift.highlighter module."""

import pytest

from logdrift.highlighter import highlight_keywords, parse_highlight_keywords


class TestParseHighlightKeywords:
    def test_returns_empty_list_for_none(self):
        assert parse_highlight_keywords(None) == []

    def test_returns_empty_list_for_empty_string(self):
        assert parse_highlight_keywords("") == []

    def test_single_keyword(self):
        assert parse_highlight_keywords("error") == ["error"]

    def test_multiple_keywords(self):
        assert parse_highlight_keywords("error,timeout,failed") == [
            "error",
            "timeout",
            "failed",
        ]

    def test_strips_whitespace(self):
        assert parse_highlight_keywords(" error , timeout ") == ["error", "timeout"]

    def test_ignores_empty_segments(self):
        assert parse_highlight_keywords("error,,failed") == ["error", "failed"]


class TestHighlightKeywords:
    def test_returns_text_unchanged_when_no_keywords(self):
        text = "some log line"
        assert highlight_keywords(text, []) == text

    def test_returns_text_unchanged_for_empty_text(self):
        assert highlight_keywords("", ["error"]) == ""

    def test_wraps_keyword_with_ansi_codes(self):
        result = highlight_keywords("an error occurred", ["error"])
        assert "error" in result
        assert "\033[" in result

    def test_case_insensitive_by_default(self):
        result = highlight_keywords("An ERROR occurred", ["error"])
        assert "\033[" in result
        assert "ERROR" in result

    def test_case_sensitive_no_match(self):
        result = highlight_keywords("An ERROR occurred", ["error"], case_sensitive=True)
        # No ANSI codes injected because case mismatch
        assert result == "An ERROR occurred"

    def test_case_sensitive_match(self):
        result = highlight_keywords("An error occurred", ["error"], case_sensitive=True)
        assert "\033[" in result

    def test_multiple_keywords_highlighted(self):
        result = highlight_keywords("error and timeout happened", ["error", "timeout"])
        assert result.count("\033[") >= 4  # at least open+reset per keyword

    def test_empty_keyword_in_list_is_skipped(self):
        result = highlight_keywords("some text", ["", "text"])
        assert "\033[" in result
        assert "text" in result

    def test_keyword_not_in_text_leaves_text_unchanged(self):
        result = highlight_keywords("all good here", ["error"])
        assert result == "all good here"
