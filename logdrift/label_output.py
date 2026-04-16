"""Output helpers for the labeler feature."""

from __future__ import annotations

from typing import Callable, Optional

from logdrift.labeler import LabelRule, parse_label_rules, label_line, inject_labels


def make_label_rules(spec: Optional[str]) -> list[LabelRule]:
    """Build label rules from a CLI spec string, or return empty list."""
    return parse_label_rules(spec) if spec else []


def apply_labels(raw: str, rules: list[LabelRule]) -> tuple[str, list[str]]:
    """Return (possibly modified line, matched labels)."""
    labels = label_line(raw, rules)
    if labels:
        return inject_labels(raw, labels), labels
    return raw, []


def write_labeled_line(
    raw: str,
    rules: list[LabelRule],
    stream,
    label_callback: Optional[Callable[[str, list[str]], None]] = None,
) -> None:
    """Apply labels to a line, write the result, and invoke optional callback."""
    if not rules:
        stream.write(raw + "\n")
        return
    modified, labels = apply_labels(raw, rules)
    stream.write(modified + "\n")
    if labels and label_callback:
        label_callback(modified, labels)
