"""Tests for logdrift.enricher."""

import json
import pytest

from logdrift.enricher import enrich_json_fields, enrich_line, parse_enrich_fields


class TestParseEnrichFields:
    def test_none_returns_empty(self):
        assert parse_enrich_fields(None) == {}

    def test_empty_string_returns_empty(self):
        assert parse_enrich_fields("") == {}

    def test_single_pair(self):
        assert parse_enrich_fields("env=prod") == {"env": "prod"}

    def test_multiple_pairs(self):
        result = parse_enrich_fields("env=prod,host=web01")
        assert result == {"env": "prod", "host": "web01"}

    def test_whitespace_stripped(self):
        result = parse_enrich_fields(" env = prod , host = web01 ")
        assert result == {"env": "prod", "host": "web01"}

    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match="Invalid enrich field"):
            parse_enrich_fields("envprod")

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="Empty key"):
            parse_enrich_fields("=prod")

    def test_value_may_contain_equals(self):
        result = parse_enrich_fields("token=abc=def")
        assert result == {"token": "abc=def"}


class TestEnrichJsonFields:
    def test_adds_missing_field(self):
        result = enrich_json_fields({"level": "info"}, {"env": "prod"})
        assert result["env"] == "prod"

    def test_does_not_overwrite_existing_field(self):
        result = enrich_json_fields({"env": "dev"}, {"env": "prod"})
        assert result["env"] == "dev"

    def test_original_dict_not_mutated(self):
        original = {"level": "info"}
        enrich_json_fields(original, {"env": "prod"})
        assert "env" not in original

    def test_empty_fields_returns_copy(self):
        original = {"level": "info"}
        result = enrich_json_fields(original, {})
        assert result == original
        assert result is not original


class TestEnrichLine:
    def test_json_line_enriched(self):
        line = json.dumps({"level": "info", "msg": "ok"})
        result = enrich_line(line, {"env": "prod"})
        data = json.loads(result)
        assert data["env"] == "prod"
        assert data["level"] == "info"

    def test_plain_text_returned_unchanged(self):
        line = "plain log line"
        assert enrich_line(line, {"env": "prod"}) == line

    def test_invalid_json_returned_unchanged(self):
        line = "{not valid json"
        assert enrich_line(line, {"env": "prod"}) == line

    def test_json_array_returned_unchanged(self):
        line = json.dumps([1, 2, 3])
        assert enrich_line(line, {"env": "prod"}) == line

    def test_empty_fields_returns_line_unchanged(self):
        line = json.dumps({"level": "warn"})
        assert enrich_line(line, {}) == line

    def test_existing_key_not_overwritten(self):
        line = json.dumps({"env": "dev"})
        result = enrich_line(line, {"env": "prod"})
        assert json.loads(result)["env"] == "dev"
