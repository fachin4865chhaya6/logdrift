"""Tests for logdrift.router."""
import json
import pytest
from unittest.mock import patch, MagicMock

from logdrift.router import RouteRule, parse_route_rules, LineRouter


JSON_ERROR = json.dumps({"level": "error", "msg": "boom"})
JSON_INFO = json.dumps({"level": "info", "msg": "ok"})
PLAIN = "plain text error line"


class TestRouteRule:
    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="pattern"):
            RouteRule(pattern="", destination="out.log")

    def test_empty_destination_raises(self):
        with pytest.raises(ValueError, match="destination"):
            RouteRule(pattern="error", destination="")

    def test_matches_plain_text(self):
        rule = RouteRule(pattern="error", destination="err.log")
        assert rule.matches(PLAIN) is True

    def test_no_match_plain_text(self):
        rule = RouteRule(pattern="critical", destination="crit.log")
        assert rule.matches(PLAIN) is False

    def test_matches_json_full_line_when_no_field(self):
        rule = RouteRule(pattern="boom", destination="err.log")
        assert rule.matches(JSON_ERROR) is True

    def test_matches_json_field_value(self):
        rule = RouteRule(pattern="error", destination="err.log", field_path="level")
        assert rule.matches(JSON_ERROR) is True

    def test_no_match_json_field_value(self):
        rule = RouteRule(pattern="error", destination="err.log", field_path="level")
        assert rule.matches(JSON_INFO) is False

    def test_missing_field_falls_back_to_empty_string(self):
        rule = RouteRule(pattern="error", destination="err.log", field_path="nonexistent")
        assert rule.matches(JSON_ERROR) is False


class TestParseRouteRules:
    def test_none_returns_empty(self):
        assert parse_route_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_route_rules("") == []

    def test_single_rule(self):
        rules = parse_route_rules("error:err.log")
        assert len(rules) == 1
        assert rules[0].pattern == "error"
        assert rules[0].destination == "err.log"

    def test_multiple_rules(self):
        rules = parse_route_rules("error:err.log, warn:warn.log")
        assert len(rules) == 2
        assert rules[1].destination == "warn.log"

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="missing ':'"):
            parse_route_rules("nodestination")


class TestLineRouter:
    def _make_router(self, rules):
        router = LineRouter(rules)
        return router

    def test_no_match_returns_none(self):
        router = LineRouter([RouteRule(pattern="critical", destination="/tmp/crit.log")])
        with patch.object(router, "_get_stream") as mock_stream:
            result = router.route(PLAIN)
        assert result is None

    def test_matching_rule_routes_line(self, tmp_path):
        dest = str(tmp_path / "err.log")
        router = LineRouter([RouteRule(pattern="error", destination=dest)])
        result = router.route(PLAIN)
        assert result == dest
        router.close()
        assert "error" in (tmp_path / "err.log").read_text()

    def test_first_matching_rule_wins(self, tmp_path):
        dest1 = str(tmp_path / "first.log")
        dest2 = str(tmp_path / "second.log")
        rules = [
            RouteRule(pattern="error", destination=dest1),
            RouteRule(pattern="error", destination=dest2),
        ]
        router = LineRouter(rules)
        result = router.route(PLAIN)
        assert result == dest1
        router.close()

    def test_close_clears_streams(self, tmp_path):
        dest = str(tmp_path / "out.log")
        router = LineRouter([RouteRule(pattern=".", destination=dest)])
        router.route("hello")
        router.close()
        assert router._streams == {}
