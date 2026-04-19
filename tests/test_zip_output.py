import json
import pytest
from logdrift.zip_output import make_zip_rules, apply_zipping


def _line(**kw) -> str:
    return json.dumps(kw)


def test_make_zip_rules_none_returns_empty():
    assert make_zip_rules(None) == []


def test_make_zip_rules_empty_returns_empty():
    assert make_zip_rules("") == []


def test_make_zip_rules_returns_rules():
    rules = make_zip_rules("a,b->out")
    assert len(rules) == 1


def test_apply_zipping_no_rules_unchanged():
    raw = _line(a=1, b=2)
    assert apply_zipping(raw, []) == raw


def test_apply_zipping_transforms_line():
    raw = _line(a=1, b=2)
    rules = make_zip_rules("a,b->pair")
    result = json.loads(apply_zipping(raw, rules))
    assert result["pair"] == [1, 2]


def test_apply_zipping_plain_text_unchanged():
    rules = make_zip_rules("a,b->out")
    assert apply_zipping("not json", rules) == "not json"
