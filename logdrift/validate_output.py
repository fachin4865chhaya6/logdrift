from __future__ import annotations
import sys
from logdrift.validator import ValidationRule, parse_validation_rules, validate_line


def make_validation_rules(spec: str | None) -> list[ValidationRule]:
    return parse_validation_rules(spec)


def apply_validation(
    raw: str,
    rules: list[ValidationRule],
    *,
    drop_invalid: bool = False,
    warn_stream=None,
) -> str | None:
    """Validate raw line. Returns raw or None if dropped. Emits warnings."""
    if not rules:
        return raw
    _, failed = validate_line(raw, rules)
    if failed:
        if warn_stream is None:
            warn_stream = sys.stderr
        tags = ", ".join(failed)
        warn_stream.write(f"[logdrift:validate] failed rules: {tags} | {raw}\n")
        if drop_invalid:
            return None
    return raw
