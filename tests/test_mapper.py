"""Tests for logdrift.mapper."""
import json
import pytest
from logdrift.mapper import FieldMapper, parse_mapper_spec, map_json_fields, map_line


def _line(**kw) -> str:
    return json.dumps(kw)


class TestFieldMapper:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            FieldMapper(field="", mapping={})

    def test_whitespace_field_raises(self):
        with pytest.raises(ValueError):
            FieldMapper(field="  ", mapping={})

    def test_non_dict_mapping_raises(self):
        with pytest.raises(TypeError):
            FieldMapper(field="level", mapping=[])  # type: ignore

    def test_apply_replaces_known_value(self):
        m = FieldMapper(field="level", mapping={"info": "INFO", "warn": "WARN"})
        result = m.apply({"level": "info", "msg": "hello"})
        assert result["level"] == "INFO"

    def test_apply_leaves_unknown_value(self):
        m = FieldMapper(field="level", mapping={"info": "INFO"})
        result = m.apply({"level": "debug"})
        assert result["level"] == "debug"

    def test_apply_leaves_missing_field(self):
        m = FieldMapper(field="level", mapping={"info": "INFO"})
        result = m.apply({"msg": "hello"})
        assert result == {"msg": "hello"}

    def test_apply_does_not_mutate_input(self):
        m = FieldMapper(field="level", mapping={"info": "INFO"})
        original = {"level": "info"}
        m.apply(original)
        assert original["level"] == "info"


class TestParseMapperSpec:
    def test_none_returns_empty(self):
        assert parse_mapper_spec(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_mapper_spec("") == []

    def test_single_spec(self):
        mappers = parse_mapper_spec('level:{"info":"INFO"}')
        assert len(mappers) == 1
        assert mappers[0].field == "level"
        assert mappers[0].mapping == {"info": "INFO"}

    def test_multiple_specs(self):
        mappers = parse_mapper_spec('level:{"info":"INFO"};env:{"prod":"production"}')
        assert len(mappers) == 2
        assert mappers[1].field == "env"

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            parse_mapper_spec("level:not-json")


class TestMapLine:
    def test_plain_text_unchanged(self):
        mappers = parse_mapper_spec('level:{"info":"INFO"}')
        assert map_line("plain text", mappers) == "plain text"

    def test_no_mappers_unchanged(self):
        line = _line(level="info")
        assert map_line(line, []) == line

    def test_json_field_mapped(self):
        mappers = parse_mapper_spec('level:{"info":"INFO"}')
        line = _line(level="info", msg="ok")
        result = json.loads(map_line(line, mappers))
        assert result["level"] == "INFO"

    def test_multiple_mappers_applied(self):
        mappers = parse_mapper_spec('level:{"info":"INFO"};env:{"prod":"production"}')
        line = _line(level="info", env="prod")
        result = json.loads(map_line(line, mappers))
        assert result["level"] == "INFO"
        assert result["env"] == "production"
