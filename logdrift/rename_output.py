from __future__ import annotations

from typing import Optional

from logdrift.renamer import parse_rename_map, rename_line


def make_rename_map(spec: Optional[str]) -> dict[str, str]:
    """Return a rename map from CLI spec, or empty dict if spec is None."""
    if not spec:
        return {}
    return parse_rename_map(spec)


def apply_rename(line: str, rename_map: dict[str, str]) -> str:
    """Apply rename map to line, returning transformed line."""
    if not rename_map:
        return line
    return rename_line(line, rename_map)
