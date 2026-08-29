"""Resolve [klipper_common] settings (pure logic, no Klipper imports)."""

from __future__ import annotations

from dataclasses import dataclass

from . import messages as msg
from .constants import LOG_LEVEL_DEFAULT, LOG_LEVELS


@dataclass(frozen=True)
class CommonSettings:
    """Resolved settings snapshot."""

    log_level: str


def resolve_settings(user: dict) -> CommonSettings:
    """Build settings from parsed user config. Raises ValueError on bad values."""
    raw = user.get("log_level", LOG_LEVEL_DEFAULT)
    if raw is None or raw == "":
        level = LOG_LEVEL_DEFAULT
    else:
        level = str(raw).strip().lower()
    if level not in LOG_LEVELS:
        raise ValueError(msg.invalid_log_level(str(raw)))
    return CommonSettings(log_level=level)
