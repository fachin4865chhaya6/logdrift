"""Tests for logdrift.config module."""

import json
import pytest
from pathlib import Path

from logdrift.config import load_config, merge_config_with_args, find_config_file


class TestLoadConfig:
    def test_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = load_config()
        assert result == {}

    def test_loads_valid_json_config(self, tmp_path):
        cfg = {"follow": True, "no_color": False}
        config_file = tmp_path / "logdrift.json"
        config_file.write_text(json.dumps(cfg))
        result = load_config(path=config_file)
        assert result == cfg

    def test_raises_on_invalid_json(self, tmp_path):
        config_file = tmp_path / "logdrift.json"
        config_file.write_text("not valid json {{{")
        with pytest.raises(ValueError, match="Failed to load config"):
            load_config(path=config_file)

    def test_raises_on_missing_explicit_path(self, tmp_path):
        missing = tmp_path / "missing.json"
        with pytest.raises(ValueError, match="Failed to load config"):
            load_config(path=missing)

    def test_loads_nested_config(self, tmp_path):
        cfg = {"regex": "ERROR", "json_filter": "level=error"}
        config_file = tmp_path / "my_config.json"
        config_file.write_text(json.dumps(cfg))
        result = load_config(path=config_file)
        assert result["regex"] == "ERROR"
        assert result["json_filter"] == "level=error"


class TestFindConfigFile:
    def test_returns_none_when_no_config_present(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = find_config_file()
        assert result is None

    def test_finds_dotfile_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".logdrift.json"
        config_file.write_text("{}")
        result = find_config_file()
        assert result == config_file


class TestMergeConfigWithArgs:
    def test_args_override_config(self):
        config = {"follow": False, "regex": "INFO"}
        args = {"regex": "ERROR", "follow": None}
        merged = merge_config_with_args(config, args)
        assert merged["regex"] == "ERROR"
        assert merged["follow"] is False

    def test_config_fills_missing_args(self):
        config = {"no_color": True}
        args = {"regex": None, "no_color": False}
        merged = merge_config_with_args(config, args)
        assert merged["no_color"] is True

    def test_empty_config_uses_args(self):
        config = {}
        args = {"follow": True, "regex": "WARN"}
        merged = merge_config_with_args(config, args)
        assert merged["follow"] is True
        assert merged["regex"] == "WARN"
