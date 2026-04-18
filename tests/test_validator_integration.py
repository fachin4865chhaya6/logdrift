import json
from logdrift.validator import parse_validation_rules, validate_line


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_pipeline_all_valid():
    spec = "level:^(INFO|WARN|ERROR)$:bad-level,status:^[12345]\\d{2}$:bad-status"
    rules = parse_validation_rules(spec)
    lines = [
        _line(level="INFO", status="200"),
        _line(level="WARN", status="404"),
        _line(level="ERROR", status="500"),
    ]
    for raw in lines:
        _, failed = validate_line(raw, rules)
        assert failed == [], f"Expected no failures for {raw}"


def test_pipeline_mixed_validity():
    spec = "level:^(INFO|WARN)$:bad-level"
    rules = parse_validation_rules(spec)
    results = []
    for raw in [_line(level="INFO"), _line(level="DEBUG"), _line(level="WARN")]:
        _, failed = validate_line(raw, rules)
        results.append(bool(failed))
    assert results == [False, True, False]


def test_plain_text_lines_always_pass():
    rules = parse_validation_rules("level:INFO")
    for raw in ["plain text", "another line", "no json here"]:
        _, failed = validate_line(raw, rules)
        assert failed == []


def test_nested_field_validation():
    rules = parse_validation_rules("meta.env:^(prod|staging)$:bad-env")
    valid = json.dumps({"meta": {"env": "prod"}})
    invalid = json.dumps({"meta": {"env": "local"}})
    _, f1 = validate_line(valid, rules)
    _, f2 = validate_line(invalid, rules)
    assert f1 == []
    assert f2 == ["bad-env"]
