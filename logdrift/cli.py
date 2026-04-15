"""CLI entry point for logdrift using argparse."""

import argparse
import sys

from logdrift.tailer import tail_file
from logdrift.formatter import format_line


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdrift",
        description="Tail and filter structured log files with regex and JSON path support.",
    )
    parser.add_argument("file", help="Path to the log file to tail.")
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        default=False,
        help="Follow the file for new lines (like tail -f).",
    )
    parser.add_argument(
        "-r", "--regex",
        metavar="PATTERN",
        default=None,
        help="Filter lines matching this regex pattern.",
    )
    parser.add_argument(
        "-j", "--json-filter",
        metavar="KEY=VALUE",
        default=None,
        help="Filter JSON lines by key path and value, e.g. 'level=error'.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colorized output.",
    )
    return parser


def parse_json_filter(json_filter: str) -> tuple[str, str] | None:
    """Parse a KEY=VALUE string into a (key, value) tuple."""
    if json_filter and "=" in json_filter:
        key, _, value = json_filter.partition("=")
        return key.strip(), value.strip()
    return None


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    json_filter_pair = parse_json_filter(args.json_filter) if args.json_filter else None

    try:
        for line in tail_file(
            path=args.file,
            follow=args.follow,
            regex_pattern=args.regex,
            json_filter=json_filter_pair,
        ):
            output = format_line(line, colorize=not args.no_color)
            print(output)
    except FileNotFoundError as exc:
        print(f"logdrift: error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
