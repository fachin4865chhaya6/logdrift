"""Tests for logdrift.map_output."""
import json
from logdrift.map_output import make_mappers, apply_mapping


def _line(**kw) -> str:
    return json.dumps(kw)


def test_make_mappers_none_returns_empty():
    assert make_mappers(None) == []


def test_make_mappers_empty_returns_empty():
    assert make_mappers("") == []


def test_make_mappers_returns_mappers():
    mappers = make_mappers('{"info":"INFO"}' )
    # invalid spec — check it raises rather than silently failing
    import pytest
    with pytest.raises(Exception):
        make_mappers("level")


def test_make_mappers_valid_spec():
    mappers = make_mappers('level:{"info":"INFO"}')
    assert len(mappers) == 1


def test_apply_mapping_no_mappers_unchanged():
    line = _line(level="info")
    assert apply_mapping(line, []) == line


def test_apply_mapping_transforms_field():
    mappers = make_mappers('level:{"info":"INFO"}')
    line = _line(level="info")
    result = json.loads(apply_mapping(line, mappers))
    assert result["level"] == "INFO"


def test_apply_mapping_plain_text_unchanged():
    mappers = make_mappers('level:{"info":"INFO"}')
    assert apply_mapping("not json", mappers) == "not json"
