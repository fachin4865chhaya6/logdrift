import json
import pytest
from logdrift.renamer import parse_rename_map, rename_json_fields, rename_line


class TestParseRenameMap:
    def test_none_returns_empty(self):
        assert parse_rename_map(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_rename_map("") == {}

    def test_single_pair(self):
        assert parse_rename_map("old:new") == {"old": "new"}

    def test_multiple_pairs(self):
        assert parse_rename_map("a:b,c:d") == {"a": "b", "c": "d"}

    def test_strips_whitespace(self):
        assert parse_rename_map(" a : b , c : d ") == {"a": "b", "c": "d"}

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="Invalid rename pair"):
            parse_rename_map("oldnew")

    def test_empty_old_key_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_rename_map(":new")

    def test_empty_new_key_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_rename_map("old:")


class TestRenameJsonFields:
    def test_renames_matching_key(self):
        result = rename_json_fields({"level": "info"}, {"level": "severity"})
        assert result == {"severity": "info"}

    def test_non_matching_key_unchanged(self):
        result = rename_json_fields({"msg": "hello"}, {"level": "severity"})
        assert result == {"msg": "hello"}

    def test_multiple_renames(self):
        result = rename_json_fields({"a": 1, "b": 2}, {"a": "x", "b": "y"})
        assert result == {"x": 1, "y": 2}

    def test_partial_rename(self):
        result = rename_json_fields({"a": 1, "c": 3}, {"a": "z"})
        assert result == {"z": 1, "c": 3}


class TestRenameLine:
    def _json(self, **kwargs) -> str:
        return json.dumps(kwargs)

    def test_renames_field_in_json_line(self):
        line = self._json(level="info", msg="hello")
        result = rename_line(line, {"level": "severity"})
        data = json.loads(result)
        assert "severity" in data
        assert "level" not in data

    def test_plain_text_returned_unchanged(self):
        line = "plain text log"
        assert rename_line(line, {"level": "severity"}) == line

    def test_json_array_returned_unchanged(self):
        line = json.dumps([1, 2, 3])
        assert rename_line(line, {"a": "b"}) == line

    def test_empty_rename_map_returns_line_unchanged(self):
        line = self._json(level="warn")
        assert rename_line(line, {}) == line

    def test_preserves_values(self):
        line = self._json(ts="2024-01-01", level="error")
        result = rename_line(line, {"ts": "timestamp"})
        data = json.loads(result)
        assert data["timestamp"] == "2024-01-01"
        assert data["level"] == "error"
