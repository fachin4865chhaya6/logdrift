"""Log line parser supporting JSON and plain text formats with JSONPath and regex filtering."""

import json
import re
from typing import Any, Optional


def parse_line(line: str) -> Optional[dict]:
    """Attempt to parse a log line as JSON. Returns None if not valid JSON."""
    line = line.strip()
    if not line:
        return None
    try:
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            return parsed
        return None
    except json.JSONDecodeError:
        return None


def get_json_path_value(data: dict, path: str) -> Any:
    """
    Retrieve a value from a nested dict using a dot-separated path.
    Example: 'level' or 'request.method'
    """
    keys = path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def matches_json_filter(data: dict, json_path: str, pattern: str) -> bool:
    """
    Check if the value at json_path in data matches the given regex pattern.
    Returns False if the path does not exist or value is not a string.
    """
    value = get_json_path_value(data, json_path)
    if value is None:
        return False
    return bool(re.search(pattern, str(value)))


def matches_regex_filter(line: str, pattern: str) -> bool:
    """Check if a raw log line matches the given regex pattern."""
    return bool(re.search(pattern, line))


def extract_fields(line: str, fields: list[str]) -> dict:
    """
    Extract specific fields from a JSON log line.

    Returns a dict with the requested fields and their values.
    Fields that are missing from the parsed JSON will be omitted.
    Returns an empty dict if the line is not valid JSON.
    """
    parsed = parse_line(line)
    if parsed is None:
        return {}
    return {field: value for field in fields if (value := get_json_path_value(parsed, field)) is not None}


def filter_line(
    line: str,
    regex: Optional[str] = None,
    json_path: Optional[str] = None,
    json_pattern: Optional[str] = None,
) -> bool:
    """
    Determine whether a log line should be included based on active filters.

    - regex: applied to the raw line string
    - json_path + json_pattern: applied to parsed JSON field value
    """
    line = line.strip()
    if not line:
        return False

    if regex and not matches_regex_filter(line, regex):
        return False

    if json_path and json_pattern:
        parsed = parse_line(line)
        if parsed is None:
            return False
        if not matches_json_filter(parsed, json_path, json_pattern):
            return False

    return True
