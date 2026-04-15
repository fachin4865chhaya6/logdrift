"""Tests for logdrift.pivot."""

import json
import pytest

from logdrift.pivot import PivotTable


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


class TestPivotTable:
    def test_empty_row_field_raises(self):
        with pytest.raises(ValueError):
            PivotTable("", "level")

    def test_empty_col_field_raises(self):
        with pytest.raises(ValueError):
            PivotTable("service", "")

    def test_add_returns_keys(self):
        pt = PivotTable("service", "level")
        result = pt.add(_line(service="api", level="error"))
        assert result == ("api", "error")

    def test_add_plain_text_returns_none(self):
        pt = PivotTable("service", "level")
        assert pt.add("not json") is None

    def test_add_missing_row_field_returns_none(self):
        pt = PivotTable("service", "level")
        assert pt.add(_line(level="info")) is None

    def test_add_missing_col_field_returns_none(self):
        pt = PivotTable("service", "level")
        assert pt.add(_line(service="api")) is None

    def test_get_returns_count(self):
        pt = PivotTable("service", "level")
        pt.add(_line(service="api", level="error"))
        pt.add(_line(service="api", level="error"))
        assert pt.get("api", "error") == 2

    def test_get_missing_key_returns_zero(self):
        pt = PivotTable("service", "level")
        assert pt.get("unknown", "debug") == 0

    def test_row_keys_sorted(self):
        pt = PivotTable("service", "level")
        pt.add(_line(service="web", level="info"))
        pt.add(_line(service="api", level="info"))
        assert pt.row_keys() == ["api", "web"]

    def test_col_keys_sorted(self):
        pt = PivotTable("service", "level")
        pt.add(_line(service="api", level="warn"))
        pt.add(_line(service="api", level="error"))
        assert pt.col_keyswarn"]

    def test_reset_clears_table(self):
        pt = PivotTable("service", "level")
        pt.add(_line(service="api", level="info"))
        pt.reset()
        assert pt.row_keys() == []
        assert pt.get("api", "info") == 0

    def test_format_table_no_data(self):
        pt = PivotTable("service", "level")
        out = pt.format_table()
        assert "no data" in out

    def test_format_table_contains_values(self):
        pt = PivotTable("service", "level")
        pt.add(_line(service="api", level="error"))
        pt.add(_line(service="api", level="info"))
        pt.add(_line(service="web", level="info"))
        out = pt.format_table()
        assert "api" in out
        assert "web" in out
        assert "error" in out
        assert "info" in out

    def test_independent_cells(self):
        pt = PivotTable("service", "level")
        for _ in range(3):
            pt.add(_line(service="api", level="error"))
        pt.add(_line(service="web", level="info"))
        assert pt.get("api", "error") == 3
        assert pt.get("web", "info") == 1
        assert pt.get("api", "info") == 0
