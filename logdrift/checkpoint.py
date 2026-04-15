"""Checkpoint support for resuming log tailing from a saved file offset."""

import json
import os
from pathlib import Path
from typing import Optional


DEFAULT_CHECKPOINT_DIR = ".logdrift"


def _checkpoint_path(log_path: str, checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR) -> Path:
    """Return the checkpoint file path for a given log file."""
    log_name = Path(log_path).name.replace("/", "_")
    return Path(checkpoint_dir) / f"{log_name}.checkpoint.json"


def load_checkpoint(log_path: str, checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR) -> Optional[int]:
    """Load the saved byte offset for a log file, or None if not found."""
    path = _checkpoint_path(log_path, checkpoint_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        offset = data.get("offset")
        if isinstance(offset, int) and offset >= 0:
            return offset
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_checkpoint(
    log_path: str,
    offset: int,
    checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR,
) -> None:
    """Persist the current byte offset for a log file."""
    if offset < 0:
        raise ValueError(f"offset must be non-negative, got {offset}")
    dir_path = Path(checkpoint_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(log_path, checkpoint_dir)
    with open(path, "w") as f:
        json.dump({"log_path": log_path, "offset": offset}, f)


def clear_checkpoint(log_path: str, checkpoint_dir: str = DEFAULT_CHECKPOINT_DIR) -> bool:
    """Delete the checkpoint file for a log file. Returns True if it existed."""
    path = _checkpoint_path(log_path, checkpoint_dir)
    if path.exists():
        path.unlink()
        return True
    return False
