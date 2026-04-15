"""CLI entry point for logdrift."""

import argparse
import sys
from typing import Any, Dict, Optional, Tuple

from logdrift.buffer import parse_context_args
from logdrift.config import load_config, merge_config_with_args
from logdrift.output import run_output
from logdrift.tailer import tail_file


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logdrift",
        description="Tail and filter structured log files.",
    )
    p.add_argument("file", help="Path to log file")
    p.add_argument("-f", "--follow", action="store_true", default=False,
                   help="Follow file like tail -f")
    p.add_argument("--regex", default=None, help="Regex filter applied to raw lines")
    p.add_argument("--json-filter", default=None,
                   help="JSON path filter e.g. level=error")
    p.add_argument("--highlight", default=None,
                   help="Comma-separated keywords to highlight")
    p.add_argument("--level", default=None, help="Minimum log level to show")
    p.add_argument("--config", default=None, help="Path to .logdrift.json config file")
    p.add_argument("--sample", type=float, default=None,
                   help="Sample rate between 0.0 and 1.0")
    p.add_argument("--redact", default=None,
                   help="Comma-separated JSON fields to redact")
    p.add_argument("--stats", action="store_true", default=False,
                   help="Print stats summary after run")
    p.add_argument("-B", "--before-context", type=int, default=None,
                   dest="before_context",
                   help="Number of lines to show before each match")
    p.add_argument("-A", "--after-context", type=int, default=None,
                   dest="after_context",
                   help="Number of lines to show after each match")
    return p


def parse_json_filter(value: Optional[str]) -> Optional[Tuple[str, str]]:
    if not value:
        return None
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"--json-filter must be in key=value format, got: {value!r}"
        )
    key, _, val = value.partition("=")
    return key.strip(), val.strip()


def run(args: argparse.Namespace) -> None:
    config = load_config(getattr(args, "config", None))
    merged = merge_config_with_args(config, args)

    json_filter = parse_json_filter(merged.get("json_filter"))
    buf = parse_context_args(
        merged.get("before_context"),
        merged.get("after_context"),
    )

    lines = tail_file(
        path=merged["file"],
        follow=merged.get("follow", False),
        regex=merged.get("regex"),
        json_filter=json_filter,
    )

    run_output(
        lines=lines,
        highlight=merged.get("highlight"),
        show_stats=merged.get("stats", False),
        sample_rate=merged.get("sample"),
        redact=merged.get("redact"),
        buffer=buf,
    )


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    try:
        run(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"logdrift: error: {exc}", file=sys.stderr)
        sys.exit(1)
