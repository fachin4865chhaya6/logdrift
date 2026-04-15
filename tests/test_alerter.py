"""Tests for logdrift.alerter."""

from __future__ import annotations

import pytest

from logdrift.alerter import AlertRule, check_alerts, parse_alert_rules


# ---------------------------------------------------------------------------
# parse_alert_rules
# ---------------------------------------------------------------------------

class TestParseAlertRules:
    def test_none_returns_empty(self):
        assert parse_alert_rules(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_alert_rules("") == []

    def test_single_rule(self):
        rules = parse_alert_rules("err:ERROR")
        assert len(rules) == 1
        assert rules[0].name == "err"
        assert rules[0].pattern.pattern == "ERROR"

    def test_multiple_rules(self):
        rules = parse_alert_rules("err:ERROR,warn:WARN")
        assert [r.name for r in rules] == ["err", "warn"]

    def test_threshold_and_window_forwarded(self):
        rules = parse_alert_rules("err:ERROR", threshold=5, window=30.0)
        assert rules[0].threshold == 5
        assert rules[0].window == 30.0

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="name:pattern"):
            parse_alert_rules("badspec")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            parse_alert_rules(":ERROR")

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError):
            parse_alert_rules("err:")

    def test_whitespace_stripped(self):
        rules = parse_alert_rules(" err : ERROR ")
        assert rules[0].name == "err"
        assert rules[0].pattern.pattern == "ERROR"


# ---------------------------------------------------------------------------
# AlertRule.record_hit
# ---------------------------------------------------------------------------

class TestAlertRule:
    def _make_rule(self, threshold=2, window=60.0):
        import re
        return AlertRule(name="test", pattern=re.compile("ERR"), threshold=threshold, window=window)

    def test_below_threshold_returns_false(self):
        rule = self._make_rule(threshold=3)
        assert rule.record_hit(now=0.0) is False
        assert rule.record_hit(now=1.0) is False

    def test_at_threshold_returns_true(self):
        rule = self._make_rule(threshold=2)
        rule.record_hit(now=0.0)
        assert rule.record_hit(now=1.0) is True

    def test_hits_outside_window_evicted(self):
        rule = self._make_rule(threshold=2, window=10.0)
        rule.record_hit(now=0.0)
        # 20 s later — old hit is evicted; only one hit in window
        assert rule.record_hit(now=20.0) is False

    def test_reset_clears_hits(self):
        rule = self._make_rule(threshold=1)
        rule.record_hit(now=0.0)
        rule.reset()
        assert rule.record_hit(now=1.0) is True  # needs fresh hit
        rule.reset()
        # after reset only one hit recorded — threshold=1 so True again
        assert rule.record_hit(now=2.0) is True


# ---------------------------------------------------------------------------
# check_alerts
# ---------------------------------------------------------------------------

class TestCheckAlerts:
    def _rules(self):
        return parse_alert_rules("err:ERROR", threshold=2, window=60.0)

    def test_no_match_no_callback(self):
        fired = []
        check_alerts("all good", self._rules(), lambda r, l: fired.append(r), now=0.0)
        assert fired == []

    def test_match_below_threshold_no_callback(self):
        fired = []
        rules = self._rules()
        check_alerts("ERROR here", rules, lambda r, l: fired.append(r), now=0.0)
        assert fired == []

    def test_match_at_threshold_fires_callback(self):
        fired = []
        rules = self._rules()
        check_alerts("ERROR here", rules, lambda r, l: fired.append(r.name), now=0.0)
        check_alerts("ERROR again", rules, lambda r, l: fired.append(r.name), now=1.0)
        assert fired == ["err"]

    def test_callback_receives_triggering_line(self):
        lines = []
        rules = parse_alert_rules("err:ERROR", threshold=1, window=60.0)
        check_alerts("ERROR boom", rules, lambda r, l: lines.append(l), now=0.0)
        assert lines == ["ERROR boom"]
