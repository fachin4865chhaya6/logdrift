"""Assign tags to log lines based on field values or regex patterns."""

from __future__ import annotations

import re
from typing import Any

from logdrift.parser import parse_line, get_json_path_value


def parse_tag_rules(raw: str | None) -> list[dict[str, str]]:
    """Parse a comma-separated list of tag rules in the form 'tag:pattern'.

    Example: ``error:ERROR,warn:WARN``
    """
    if not raw:
        return []
    rules: list[dict[str, str]] = []
    for part in raw.split(","):
        part = part.strip()
        if ":" not in part:
            raise ValueError(f"Invalid tag rule (expected 'tag:pattern'): {part!r}")
        tag, _, pattern = part.partition(":")
        tag = tag.strip()
        pattern = pattern.strip()
        if not tag or not pattern:
            raise ValueError(f"Tag and pattern must be non-empty in rule: {part!r}")
        rules.append({"tag": tag, "pattern": pattern})
    return rules


def tag_line(
    line: str,
    rules: list[dict[str, str]],
    field: str | None = None,
) -> list[str]:
    """Return a list of tags that match *line*.

    If *field* is given the pattern is matched against the value at that JSON
    path; otherwise the raw line text is used.
    """
    if not rules:
        return []

    parsed = parse_line(line)

    matched_tags: list[str] = []
    for rule in rules:
        tag = rule["tag"]
        pattern = rule["pattern"]
        if field and parsed is not None:
            target = get_json_path_value(parsed, field)
            text = str(target) if target is not None else ""
        else:
            text = line

        if re.search(pattern, text):
            matched_tags.append(tag)

    return matched_tags


def inject_tags(line: str, tags: list[str]) -> str:
    """Return a version of *line* with a ``_tags`` field injected.

    For JSON lines the field is added to the object.  For plain-text lines a
    ``[tag1,tag2]`` prefix is prepended.
    """
    if not tags:
        return line

    parsed = parse_line(line)
    if parsed is not None:
        import json
        parsed["_tags"] = tags
        return json.dumps(parsed)

    prefix = "[" + ",".join(tags) + "] "
    return prefix + line
