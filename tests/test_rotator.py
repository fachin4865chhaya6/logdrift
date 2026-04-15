"""Tests for logdrift.rotator — log rotation detection."""

import os
import pytest
from pathlib import Path

from logdrift.rotator import RotationDetector, make_rotation_detector


class TestRotationDetector:
    def test_no_rotation_when_file_unchanged(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("line1\n")
        detector = RotationDetector(str(f))
        assert not detector.has_rotated()

    def test_detects_truncation(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("line1\nline2\nline3\n")
        detector = RotationDetector(str(f))
        f.write_text("")  # truncate
        assert detector.has_rotated()

    def test_detects_inode_change(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("original\n")
        detector = RotationDetector(str(f))
        # Simulate rotation: delete and recreate
        f.unlink()
        f.write_text("new content\n")
        assert detector.has_rotated()

    def test_reset_clears_rotation_state(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("line1\n")
        detector = RotationDetector(str(f))
        f.write_text("")  # truncate
        assert detector.has_rotated()
        detector.reset()
        assert not detector.has_rotated()

    def test_inode_stored_on_init(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("data\n")
        detector = RotationDetector(str(f))
        expected_inode = os.stat(str(f)).st_ino
        assert detector.inode == expected_inode

    def test_size_stored_on_init(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("hello\n")
        detector = RotationDetector(str(f))
        expected_size = os.stat(str(f)).st_size
        assert detector.size == expected_size

    def test_missing_file_on_init_sets_none_inode(self, tmp_path: Path) -> None:
        detector = RotationDetector(str(tmp_path / "nonexistent.log"))
        assert detector.inode is None
        assert detector.size == 0

    def test_has_rotated_returns_false_if_file_missing_now(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("data\n")
        detector = RotationDetector(str(f))
        f.unlink()
        # File is gone — we treat this as not-yet-rotated (caller handles missing)
        assert not detector.has_rotated()

    def test_make_rotation_detector_returns_instance(self, tmp_path: Path) -> None:
        f = tmp_path / "app.log"
        f.write_text("x\n")
        detector = make_rotation_detector(str(f))
        assert isinstance(detector, RotationDetector)
