"""Integration tests for the field joiner pipeline."""
from __future__ import annotations

import json

from logdrift.joiner import join_line, parse_join_rules


def _line(**kwargs) -> str:
    return json.dumps(kwargs)


def test_chained_rules_applied_in_order():
    """Multiple rules are applied sequentially; later rules can use earlier outputs."""
    rules = parse_join_rules("full=first,last; greeting=salutation,full| ")
    raw = _line(first="Alan", last="Turing", salutation="Dr.")
    result = json.loads(join_line(raw, rules))
    assert result["full"] == "Alan Turing"
    assert result["greeting"] == "Dr. Alan Turing"


def test_unrelated_fields_preserved():
    rules = parse_join_rules("full=first,last")
    raw = _line(first="Dennis", last="Ritchie", lang="C")
    result = json.loads(join_line(raw, rules))
    assert result["lang"] == "C"
    assert result["first"] == "Dennis"


def test_empty_sep_concatenates_without_space():
    rules = parse_join_rules("token=prefix,suffix|")
    raw = _line(prefix="foo", suffix="bar")
    result = json.loads(join_line(raw, rules))
    assert result["token"] == "foobar"


def test_pipeline_plain_text_passes_through():
    rules = parse_join_rules("full=a,b")
    assert join_line("2024-01-01 INFO booting", rules) == "2024-01-01 INFO booting"
