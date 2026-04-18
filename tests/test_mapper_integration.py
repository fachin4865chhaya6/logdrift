"""Integration tests for the mapper pipeline."""
import json
from logdrift.mapper import parse_mapper_spec, map_line


def _line(**kw) -> str:
    return json.dumps(kw)


def test_chained_mappers_applied_in_order():
    spec = 'level:{"1":"one","2":"two"};status:{"ok":"OK"}'
    mappers = parse_mapper_spec(spec)
    line = _line(level="1", status="ok", msg="hello")
    result = json.loads(map_line(line, mappers))
    assert result["level"] == "one"
    assert result["status"] == "OK"
    assert result["msg"] == "hello"


def test_mapper_preserves_unrelated_fields():
    mappers = parse_mapper_spec('level:{"info":"INFO"}')
    line = _line(level="info", request_id="abc-123", latency=42)
    result = json.loads(map_line(line, mappers))
    assert result["request_id"] == "abc-123"
    assert result["latency"] == 42


def test_mapper_numeric_value_as_key():
    mappers = parse_mapper_spec('code:{"200":"OK","404":"Not Found"}')
    line = _line(code=200)
    result = json.loads(map_line(line, mappers))
    # int 200 -> str "200" lookup
    assert result["code"] == "OK"


def test_no_match_leaves_field_intact():
    mappers = parse_mapper_spec('level:{"info":"INFO"}')
    line = _line(level="error")
    result = json.loads(map_line(line, mappers))
    assert result["level"] == "error"
