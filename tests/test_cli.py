"""Tests for logdrift.cli module."""

import pytest
from unittest.mock import patch, MagicMock

from logdrift.cli import build_parser, parse_json_filter, run


class TestBuildParser:
    def test_file_argument_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_file_argument_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["app.log"])
        assert args.file == "app.log"

    def test_follow_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["app.log"])
        assert args.follow is False

    def test_follow_flag_set(self):
        parser = build_parser()
        args = parser.parse_args(["app.log", "-f"])
        assert args.follow is True

    def test_regex_option(self):
        parser = build_parser()
        args = parser.parse_args(["app.log", "-r", "ERROR"])
        assert args.regex == "ERROR"

    def test_json_filter_option(self):
        parser = build_parser()
        args = parser.parse_args(["app.log", "-j", "level=error"])
        assert args.json_filter == "level=error"

    def test_no_color_flag(self):
        parser = build_parser()
        args = parser.parse_args(["app.log", "--no-color"])
        assert args.no_color is True


class TestParseJsonFilter:
    def test_valid_key_value(self):
        result = parse_json_filter("level=error")
        assert result == ("level", "error")

    def test_value_with_equals_sign(self):
        result = parse_json_filter("msg=hello=world")
        assert result == ("msg", "hello=world")

    def test_no_equals_returns_none(self):
        result = parse_json_filter("levelonly")
        assert result is None

    def test_none_input_returns_none(self):
        result = parse_json_filter(None)
        assert result is None


class TestRun:
    def test_returns_1_on_file_not_found(self, tmp_path):
        result = run([str(tmp_path / "nonexistent.log")])
        assert result == 1

    def test_returns_0_on_success(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text('{"level": "info", "msg": "started"}\n')
        result = run([str(log_file)])
        assert result == 0

    def test_output_printed(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text('{"level": "info", "msg": "hello"}\n')
        run([str(log_file), "--no-color"])
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_regex_filter_applied(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            '{"level": "info", "msg": "keep this"}\n'
            '{"level": "debug", "msg": "drop this"}\n'
        )
        run([str(log_file), "-r", "keep", "--no-color"])
        captured = capsys.readouterr()
        assert "keep this" in captured.out
        assert "drop this" not in captured.out
