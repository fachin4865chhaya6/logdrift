"""Assigns severity labels to log lines based on field thresholds or patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from logdrift.parser import parse_line, get_json_path_value


@dataclass
class LabelRule:
    label: str
    json_path: Optional[str] = None
    pattern: Optional[str] = None
    threshold: Optional[float] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("label must not be empty")
        if self.pattern:
            self._compiled = re.compile(self.pattern)


def parse_label_rules(spec: Optional[str]) -> list[LabelRule]:
    """Parse label rules from a spec string.

    Format: ``label:path=value`` or ``label:pattern=regex``
    Multiple rules separated by commas.
    """
    if not spec:
        return []
    rules: list[LabelRule] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":path=" in part:
            label, rest = part.split(":path=", 1)
            rules.append(LabelRule(label=label.strip(), json_path=rest.strip()))
        elif ":pattern=" in part:
            label, rest = part.split(":pattern=", 1)
            rules.append(LabelRule(label=label.strip(), pattern=rest.strip()))
        elif ":threshold=" in part:
            label, rest = part.split(":threshold=", 1)
            json_path, threshold = rest.split(">", 1)
            rules.append(LabelRule(label=label.strip(), json_path=json_path.strip(), threshold=float(threshold.strip())))
        else:
            raise ValueError(f"Invalid label rule: {part!r}")
    return rules


def label_line(raw: str, rules: list[LabelRule]) -> list[str]:
    """Return list of labels that match the given raw log line."""
    if not rules:
        return []
    data = parse_line(raw)
    matched: list[str] = []
    for rule in rules:
        if rule.threshold is not None and rule.json_path and data:
            val = get_json_path_value(data, rule.json_path)
            try:
                if float(val) > rule.threshold:
                    matched.append(rule.label)
            except (TypeError, ValueError):
                pass
        elif rule.json_path and data:
            val = get_json_path_value(data, rule.json_path)
            if val is not None:
                matched.append(rule.label)
        elif rule._compiled:
            if rule._compiled.search(raw):
                matched.append(rule.label)
    return matched


def inject_labels(raw: str, labels: list[str]) -> str:
    """Inject matched labels into a JSON log line under the '_labels' key."""
    if not labels:
        return raw
    import json
    data = parse_line(raw)
    if data is None:
        return raw
    data["_labels"] = labels
    return json.dumps(data)
