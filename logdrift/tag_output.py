"""Helpers for integrating the tagger into the logdrift output pipeline."""

from __future__ import annotations

from typing import IO

from logdrift.tagger import parse_tag_rules, tag_line, inject_tags


def make_tag_rules(raw: str | None) -> list[dict[str, str]]:
    """Return parsed tag rules or an empty list when *raw* is falsy."""
    return parse_tag_rules(raw) if raw else []


def apply_tags(
    line: str,
    rules: list[dict[str, str]],
    field: str | None = None,
    inject: bool = False,
) -> tuple[str, list[str]]:
    """Compute tags for *line* and optionally inject them into the line.

    Returns a ``(processed_line, tags)`` tuple.  When *inject* is ``False``
    the returned line is identical to the input.
    """
    tags = tag_line(line, rules, field=field)
    if inject and tags:
        line = inject_tags(line, tags)
    return line, tags


def write_tagged_line(
    line: str,
    rules: list[dict[str, str]],
    stream: IO[str],
    field: str | None = None,
    inject: bool = False,
    filter_tags: list[str] | None = None,
) -> bool:
    """Write *line* to *stream* when it matches the tag filter.

    *filter_tags* – if provided, the line is only written when at least one
    of its tags appears in *filter_tags*.  Pass ``None`` to disable filtering.

    Returns ``True`` if the line was written.
    """
    processed, tags = apply_tags(line, rules, field=field, inject=inject)

    if filter_tags is not None:
        if not any(t in filter_tags for t in tags):
            return False

    stream.write(processed + "\n")
    return True
