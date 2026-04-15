"""CLI entry point for logdrift."""

import argparse
import sys
from typing import Dict, Optional

from logdrift.config import find_config_file, load_config, merge_config_with_args
from logdrift.output import run_output
from logdrift.redactor import parse_redact_fields, parse_redact_patterns
from logdrift.sampler import make_sampler, parse_sample_rate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdrift",
        description="Tail and filter structured log files.",
    )
    parser.add_argument("file", help="Path to the log file to tail")
    parser.add_argument("-f", "--follow", action="store_true", default=False,
                        help="Follow the file for new lines")
    parser.add_argument("--regex", default=None, help="Regex filter applied to each line")
    parser.add_argument("--json-filter", default=None,
                        help="JSON path filter in the form key=value")
    parser.add_argument("--level", default=None, help="Minimum log level to display")
    parser.add_argument("--highlight", default=None,
                        help="Comma-separated keywords to highlight")
    parser.add_argument("--sample", default=None, type=float,
                        help="Sample rate between 0.0 and 1.0")
    parser.add_argument("--config", default=None, help="Path to a JSON config file")
    parser.add_argument("--stats", action="store_true", default=False,
                        help="Print summary statistics after tailing")
    parser.add_argument("--redact-fields", default=None,
                        help="Comma-separated JSON field names to redact")
    parser.add_argument("--redact-patterns", default=None,
                        help="Comma-separated built-in pattern names to redact (email, ipv4, bearer, credit_card)")
    return parser


def parse_json_filter(value: Optional[str]) -> Optional[Dict[str, str]]:
    if not value:
        return None
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"--json-filter must be in key=value format, got: {value!r}"
        )
    key, _, val = value.partition("=")
    return {key.strip(): val.strip()}


def run(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = args.config or find_config_file()
    config = load_config(config_path)
    args = merge_config_with_args(config, args)

    json_filter = parse_json_filter(getattr(args, "json_filter", None))
    sample_rate = parse_sample_rate(getattr(args, "sample", None))
    sampler = make_sampler(sample_rate)

    redact_fields = parse_redact_fields(getattr(args, "redact_fields", None))
    redact_patterns_list = parse_redact_patterns(getattr(args, "redact_patterns", None))

    run_output(
        filepath=args.file,
        follow=args.follow,
        regex=getattr(args, "regex", None),
        json_filter=json_filter,
        level=getattr(args, "level", None),
        highlight=getattr(args, "highlight", None),
        sampler=sampler,
        show_stats=getattr(args, "stats", False),
        redact_fields=redact_fields,
        redact_patterns=redact_patterns_list,
    )


def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
