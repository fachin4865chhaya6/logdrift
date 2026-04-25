"""Configuration loading for logdrift from a TOML or JSON config file."""

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATHS = [
    Path(".logdrift.json"),
    Path("logdrift.json"),
    Path(os.path.expanduser("~/.config/logdrift/config.json")),
]


def _load_json_file(path: Path) -> dict[str, Any]:
    """Load and parse a JSON config file."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_config_file() -> Path | None:
    """Search default locations for a config file."""
    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.exists():
            return candidate
    return None


def load_config(path: Path | None = None) -> dict[str, Any]:
    """
    Load logdrift configuration.

    If *path* is given, load that file. Otherwise search default locations.
    Returns an empty dict if no config file is found.
    """
    config_path = path or find_config_file()
    if config_path is None:
        return {}

    try:
        data = _load_json_file(config_path)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse config file {config_path} as JSON: {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Failed to read config file {config_path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Config file {config_path} must contain a JSON object at the top level, "
            f"got {type(data).__name__}"
        )

    return data


def merge_config_with_args(config: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """
    Merge config file values with CLI argument values.
    CLI arguments take precedence over config file values.
    """
    merged = {**config}
    for key, value in args.items():
        if value is not None and value is not False:
            merged[key] = value
        elif key not in merged:
            merged[key] = value
    return merged
