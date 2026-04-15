"""Redaction module for masking sensitive fields in log lines."""

import re
from typing import Any, Dict, List, Optional


DEFAULT_MASK = "***REDACTED***"

_BUILTIN_PATTERNS: Dict[str, str] = {
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "bearer": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
}


def parse_redact_fields(fields_str: Optional[str]) -> List[str]:
    """Parse a comma-separated string of JSON field names to redact."""
    if not fields_str:
        return []
    return [f.strip() for f in fields_str.split(",") if f.strip()]


def redact_json_fields(
    data: Dict[str, Any],
    fields: List[str],
    mask: str = DEFAULT_MASK,
) -> Dict[str, Any]:
    """Return a copy of *data* with the given field values replaced by *mask*."""
    if not fields:
        return data
    result = dict(data)
    for field in fields:
        if field in result:
            result[field] = mask
    return result


def redact_patterns(
    text: str,
    pattern_names: List[str],
    mask: str = DEFAULT_MASK,
) -> str:
    """Replace occurrences of named built-in patterns inside *text* with *mask*."""
    for name in pattern_names:
        pattern = _BUILTIN_PATTERNS.get(name)
        if pattern:
            text = re.sub(pattern, mask, text)
    return text


def parse_redact_patterns(patterns_str: Optional[str]) -> List[str]:
    """Parse a comma-separated list of built-in pattern names."""
    if not patterns_str:
        return []
    return [p.strip() for p in patterns_str.split(",") if p.strip()]


def redact_line(
    line: str,
    parsed: Optional[Dict[str, Any]],
    fields: List[str],
    patterns: List[str],
    mask: str = DEFAULT_MASK,
) -> tuple:
    """Apply field and pattern redaction to a log line.

    Returns (redacted_line, redacted_parsed).
    """
    redacted_parsed = None
    if parsed is not None and fields:
        redacted_parsed = redact_json_fields(parsed, fields, mask)
        import json
        line = json.dumps(redacted_parsed)
    if patterns:
        line = redact_patterns(line, patterns, mask)
        if redacted_parsed is not None:
            import json
            try:
                redacted_parsed = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                pass
    return line, redacted_parsed
