"""Resolve [klipper_extras] settings (pure logic, no Klipper imports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import messages as msg
from .constants import LOG_LEVEL_DEFAULT, LOG_LEVELS


@dataclass(frozen=True)
class CommonSettings:
    """Resolved settings snapshot."""

    log_level: str
    min_nozzle_temp: Optional[float] = None


def resolve_settings(user: dict) -> CommonSettings:
    """Build settings from parsed user config. Raises ValueError on bad values."""
    raw = user.get("log_level", LOG_LEVEL_DEFAULT)
    if raw is None or raw == "":
        level = LOG_LEVEL_DEFAULT
    else:
        level = str(raw).strip().lower()
    if level not in LOG_LEVELS:
        raise ValueError(msg.invalid_log_level(str(raw)))
    min_nozzle_temp = None
    if "min_nozzle_temp" in user:
        temp_raw = user["min_nozzle_temp"]
        if temp_raw is not None and str(temp_raw).strip() != "":
            if isinstance(temp_raw, bool):
                raise ValueError(msg.invalid_min_nozzle_temp(temp_raw))
            try:
                min_nozzle_temp = float(temp_raw)
            except (TypeError, ValueError) as e:
                raise ValueError(msg.invalid_min_nozzle_temp(temp_raw)) from e
    return CommonSettings(log_level=level, min_nozzle_temp=min_nozzle_temp)
