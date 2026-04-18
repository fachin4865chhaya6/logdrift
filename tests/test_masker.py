"""Tests for logdrift.masker and logdrift.mask_output."""
import json
import pytest

from logdrift.masker import MaskRule, parse_mask_rules, mask_json_fields, mask_line
from logdrift.mask_output import make_mask_rules, apply_masking


# ---------------------------------------------------------------------------
# MaskRule
# ---------------------------------------------------------------------------

class TestMaskRule:
    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            MaskRule(field_name="")

    def test_negative_keep_chars_raises(self):
        with pytest.raises(ValueError):
            MaskRule(field_name="token", keep_chars=-1)

    def test_multi_char_mask_char_raises(self):
        with pytest.raises(ValueError):
            MaskRule(field_name="token", mask_char="**")

    def test_apply_keeps_last_n_chars(self):
        rule = MaskRule(field_name="token", keep_chars=4)
        assert rule.apply("abcdefgh") == "****efgh"

    def test_apply_keep_zero_masks_all(self):
        rule = MaskRule(field_name="token", keep_chars=0)
        assert rule.apply("secret") == "******"

    def test_apply_short_value_fully_masked(self):
        rule = MaskRule(field_name="token", keep_chars=4)
        assert rule.apply("abc") == "***"

    def test_custom_mask_char(self):
        rule = MaskRule(field_name="pw", keep_chars=2, mask_char="#")
        assert rule.apply("password") == "######rd"


# ---------------------------------------------------------------------------
# parse_mask_rules
# ---------------------------------------------------------------------------

def test_none_returns_empty():
    assert parse_mask_rules(None) == []

def test_empty_string_returns_empty():
    assert parse_mask_rules("") == []

def test_single_field_default_keep():
    rules = parse_mask_rules("token")
    assert len(rules) == 1
    assert rules[0].field_name == "token"
    assert rules[0].keep_chars == 4

def test_single_field_with_keep():
    rules = parse_mask_rules("token:2")
    assert rules[0].keep_chars == 2

def test_multiple_fields():
    rules = parse_mask_rules("token:3,password:0")
    assert len(rules) == 2
    assert rules[0].field_name == "token"
    assert rules[1].field_name == "password"


# ---------------------------------------------------------------------------
# mask_json_fields
# ---------------------------------------------------------------------------

def test_masks_present_field():
    data = {"token": "abcdefgh", "level": "info"}
    rules = [MaskRule(field_name="token", keep_chars=4)]
    result = mask_json_fields(data, rules)
    assert result["token"] == "****efgh"
    assert result["level"] == "info"

def test_ignores_missing_field():
    data = {"level": "info"}
    rules = [MaskRule(field_name="token")]
    result = mask_json_fields(data, rules)
    assert "token" not in result


# ---------------------------------------------------------------------------
# mask_line
# ---------------------------------------------------------------------------

def test_plain_text_returned_unchanged():
    rules = [MaskRule(field_name="token")]
    assert mask_line("plain text", rules) == "plain text"

def test_json_line_field_masked():
    line = json.dumps({"token": "supersecret", "msg": "hi"})
    rules = [MaskRule(field_name="token", keep_chars=2)]
    result = json.loads(mask_line(line, rules))
    assert result["token"].endswith("et")
    assert result["msg"] == "hi"

def test_no_rules_returns_original():
    line = json.dumps({"token": "secret"})
    assert mask_line(line, []) == line


# ---------------------------------------------------------------------------
# mask_output helpers
# ---------------------------------------------------------------------------

def test_make_mask_rules_none():
    assert make_mask_rules(None) == []

def test_apply_masking_no_rules():
    line = json.dumps({"token": "secret"})
    assert apply_masking(line, []) == line

def test_apply_masking_masks_field():
    line = json.dumps({"token": "abcdef"})
    rules = make_mask_rules("token:0")
    result = json.loads(apply_masking(line, rules))
    assert result["token"] == "******"
