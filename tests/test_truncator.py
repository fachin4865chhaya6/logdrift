"""Tests for logdrift.truncator."""
import json
import pytest

from logdrift.truncator import parse_truncate_fields, truncate_json_fields, truncate_line


class TestParseTruncateFields:
    def test_none_returns_empty(self):
        assert parse_truncate_fields(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_truncate_fields("") == {}

    def test_single_field(self):
        assert parse_truncate_fields("message:80") == {"message": 80}

    def test_multiple_fields(self):
        result = parse_truncate_fields("message:80,trace:20")
        assert result == {"message": 80, "trace": 20}

    def test_strips_whitespace(self):
        assert parse_truncate_fields(" message : 50 ") == {"message": 50}

    def test_missing_colon_raises(self):
        with pytest.raises(ValueError, match="missing ':'"):
            parse_truncate_fields("message80")

    def test_empty_field_name_raises(self):
        with pytest.raises(ValueError, match="Empty field name"):
            parse_truncate_fields(":50")

    def test_non_integer_length_raises(self):
        with pytest.raises(ValueError, match="Non-integer"):
            parse_truncate_fields("message:abc")

    def test_zero_length_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_truncate_fields("message:0")

    def test_negative_length_raises(self):
        with pytest.raises(ValueError, match="positive"):
            parse_truncate_fields("message:-1")


class TestTruncateJsonFields:
    def test_short_value_unchanged(self):
        data = {"msg": "hello"}
        assert truncate_json_fields(data, {"msg": 10}) == {"msg": "hello"}

    def test_long_value_truncated(self):
        data = {"msg": "hello world"}
        result = truncate_json_fields(data, {"msg": 5})
        assert result["msg"] == "hello…"

    def test_non_string_field_unchanged(self):
        data = {"count": 42}
        assert truncate_json_fields(data, {"count": 1}) == {"count": 42}

    def test_missing_field_ignored(self):
        data = {"level": "info"}
        result = truncate_json_fields(data, {"msg": 5})
        assert result == {"level": "info"}

    def test_original_dict_not_mutated(self):
        data = {"msg": "hello world"}
        truncate_json_fields(data, {"msg": 3})
        assert data["msg"] == "hello world"


class TestTruncateLine:
    def test_plain_text_returned_as_is(self):
        assert truncate_line("plain text", {"msg": 5}) == "plain text"

    def test_empty_fields_returns_raw(self):
        raw = json.dumps({"msg": "hello world"})
        assert truncate_line(raw, {}) == raw

    def test_json_field_truncated(self):
        raw = json.dumps({"msg": "hello world", "level": "info"})
        result = truncate_line(raw, {"msg": 5})
        parsed = json.loads(result)
        assert parsed["msg"] == "hello…"
        assert parsed["level"] == "info"

    def test_json_array_returned_as_is(self):
        raw = json.dumps([1, 2, 3])
        assert truncate_line(raw, {"msg": 5}) == raw
