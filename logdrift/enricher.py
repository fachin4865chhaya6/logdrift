"""Field enrichment: inject derived or static fields into parsed JSON log lines."""

from __future__ import annotations

import json
from typing import Any


def parse_enrich_fields(raw: str | None) -> dict[str, str]:
    """Parse a comma-separated list of key=value pairs into a dict.

    Example: "env=prod,host=web01" -> {"env": "prod", "host": "web01"}
    """
    if not raw:
        return {}
    result: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid enrich field (expected key=value): {part!r}")
        key, _, value = part.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Empty key in enrich field: {part!r}")
        result[key] = value
    return result


def enrich_json_fields(data: dict[str, Any], fields: dict[str, str]) -> dict[str, Any]:
    """Return a new dict with extra fields merged in (existing keys are NOT overwritten)."""
    enriched = dict(data)
    for key, value in fields.items():
        if key not in enriched:
            enriched[key] = value
    return enriched


def enrich_line(line: str, fields: dict[str, str]) -> str:
    """Enrich a log line string with static fields.

    - If the line is valid JSON object, inject missing fields and return serialised JSON.
    - Otherwise return the line unchanged.
    """
    if not fields:
        return line
    stripped = line.strip()
    if not stripped.startswith("{"):
        return line
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return line
    if not isinstance(data, dict):
        return line
    enriched = enrich_json_fields(data, fields)
    return json.dumps(enriched)
