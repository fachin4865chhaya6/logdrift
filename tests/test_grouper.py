import pytest
from logdrift.grouper import LineGrouper, parse_group_field, make_grouper
import json


def _line(data: dict) -> str:
    return json.dumps(data)


class TestLineGrouper:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError, match="group_field"):
            LineGrouper(group_field="")

    def test_zero_max_groups_raises(self):
        with pytest.raises(ValueError, match="max_groups"):
            LineGrouper(group_field="level", max_groups=0)

    def test_add_plain_text_returns_none(self):
        g = LineGrouper(group_field="level")
        assert g.add("plain text") is None

    def test_add_missing_field_returns_none(self):
        g = LineGrouper(group_field="level")
        assert g.add(_line({"msg": "hi"})) is None

    def test_add_returns_bucket_key(self):
        g = LineGrouper(group_field="level")
        key = g.add(_line({"level": "info", "msg": "ok"}))
        assert key == "info"

    def test_lines_grouped_by_field(self):
        g = LineGrouper(group_field="level")
        g.add(_line({"level": "info", "msg": "a"}))
        g.add(_line({"level": "error", "msg": "b"}))
        g.add(_line({"level": "info", "msg": "c"}))
        assert len(g.get_group("info")) == 2
        assert len(g.get_group("error")) == 1

    def test_get_group_missing_key_returns_empty(self):
        g = LineGrouper(group_field="level")
        assert g.get_group("debug") == []

    def test_max_groups_enforced(self):
        g = LineGrouper(group_field="level", max_groups=2)
        g.add(_line({"level": "info"}))
        g.add(_line({"level": "error"}))
        result = g.add(_line({"level": "debug"}))
        assert result is None
        assert "debug" not in g.groups

    def test_groups_property_returns_copy(self):
        g = LineGrouper(group_field="level")
        g.add(_line({"level": "info"}))
        snapshot = g.groups
        g.add(_line({"level": "info"}))
        assert len(snapshot["info"]) == 1

    def test_format_summary_lists_groups(self):
        g = LineGrouper(group_field="level")
        g.add(_line({"level": "info"}))
        g.add(_line({"level": "error"}))
        summary = g.format_summary()
        assert "info" in summary
        assert "error" in summary
        assert "1 line(s)" in summary


class TestParseGroupField:
    def test_none_returns_none(self):
        assert parse_group_field(None) is None

    def test_empty_returns_none(self):
        assert parse_group_field("") is None

    def test_whitespace_returns_none(self):
        assert parse_group_field("   ") is None

    def test_valid_returns_stripped(self):
        assert parse_group_field("  level  ") == "level"


class TestMakeGrouper:
    def test_none_returns_none(self):
        assert make_grouper(None) is None

    def test_empty_returns_none(self):
        assert make_grouper("") is None

    def test_valid_returns_grouper(self):
        g = make_grouper("level")
        assert g is not None
        assert g.group_field == "level"

    def test_max_groups_passed(self):
        g = make_grouper("level", max_groups=5)
        assert g.max_groups == 5
