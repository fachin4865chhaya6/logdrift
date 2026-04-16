"""Tests for logdrift.checkpoint."""

import json
import pytest
from pathlib import Path

from logdrift.checkpoint import (
    load_checkpoint,
    save_checkpoint,
    clear_checkpoint,
    _checkpoint_path,
)


@pytest.fixture
def tmp_checkpoint_dir(tmp_path):
    return str(tmp_path / "checkpoints")


class TestLoadCheckpoint:
    def test_returns_none_when_no_file(self, tmp_checkpoint_dir):
        result = load_checkpoint("/var/log/app.log", tmp_checkpoint_dir)
        assert result is None

    def test_returns_saved_offset(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 1024, tmp_checkpoint_dir)
        result = load_checkpoint("/var/log/app.log", tmp_checkpoint_dir)
        assert result == 1024

    def test_returns_zero_offset(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 0, tmp_checkpoint_dir)
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) == 0

    def test_returns_none_for_invalid_json(self, tmp_checkpoint_dir):
        path = _checkpoint_path("/var/log/app.log", tmp_checkpoint_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not-json")
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) is None

    def test_returns_none_when_offset_missing_from_json(self, tmp_checkpoint_dir):
        path = _checkpoint_path("/var/log/app.log", tmp_checkpoint_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"log_path": "/var/log/app.log"}))
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) is None

    def test_returns_none_for_negative_offset_in_file(self, tmp_checkpoint_dir):
        path = _checkpoint_path("/var/log/app.log", tmp_checkpoint_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"offset": -5}))
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) is None


class TestSaveCheckpoint:
    def test_creates_checkpoint_file(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 512, tmp_checkpoint_dir)
        path = _checkpoint_path("/var/log/app.log", tmp_checkpoint_dir)
        assert path.exists()

    def test_checkpoint_contains_correct_data(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 2048, tmp_checkpoint_dir)
        path = _checkpoint_path("/var/log/app.log", tmp_checkpoint_dir)
        data = json.loads(path.read_text())
        assert data["offset"] == 2048
        assert data["log_path"] == "/var/log/app.log"

    def test_creates_directory_if_missing(self, tmp_path):
        new_dir = str(tmp_path / "nested" / "checkpoints")
        save_checkpoint("/var/log/app.log", 100, new_dir)
        assert Path(new_dir).exists()

    def test_raises_on_negative_offset(self, tmp_checkpoint_dir):
        with pytest.raises(ValueError, match="non-negative"):
            save_checkpoint("/var/log/app.log", -1, tmp_checkpoint_dir)

    def test_overwrites_existing_checkpoint(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 100, tmp_checkpoint_dir)
        save_checkpoint("/var/log/app.log", 999, tmp_checkpoint_dir)
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) == 999

    def test_different_logs_have_separate_checkpoints(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 100, tmp_checkpoint_dir)
        save_checkpoint("/var/log/other.log", 200, tmp_checkpoint_dir)
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) == 100
        assert load_checkpoint("/var/log/other.log", tmp_checkpoint_dir) == 200


class TestClearCheckpoint:
    def test_removes_existing_checkpoint(self, tmp_checkpoint_dir):
        save_checkpoint("/var/log/app.log", 512, tmp_checkpoint_dir)
        clear_checkpoint("/var/log/app.log", tmp_checkpoint_dir)
        assert load_checkpoint("/var/log/app.log", tmp_checkpoint_dir) is None

    def test_does_not_raise_when_no_checkpoint(self, tmp_checkpoint_dir):
        # Should be a no-op when the checkpoint file doesn't exist
        clear_checkpoint("/var/log/app.log", tmp_checkpoint_dir)
