"""Shared named constants for klipper_extras host (pure defs, no Klipper imports).

Host-only: version, log levels, host option keys. Feature literals live in
``features/<name>/``. Call sites import names from here instead of hardcoding.

User-facing strings stay in ``messages.py``.
"""

from __future__ import annotations

from typing import Optional

# Plugin identity (console banner, logs). Single source for packaging too
# (pyproject.toml dynamic version → this attr). Bump here only.
KLIPPER_EXTRAS_VERSION = "0.0.1"

# Klipper extra / object name: section [klipper_extras], extras path, logs.
EXTRA_NAME = "klipper_extras"


def extra_object(kind: Optional[str] = None) -> str:
    """Klipper object name (no brackets): host or ``klipper_extras <kind>``."""
    if kind:
        return "%s %s" % (EXTRA_NAME, kind)
    return EXTRA_NAME

# Seconds after klippy:ready before console banner via gcode.respond_info.
# Moonraker only calls gcode/subscribe_output after it observes READY (poll
# interval ~0.25s); messages during the ready callback never reach the web console.
ANNOUNCE_CONSOLE_DELAY = 1.0

# Plugin log_level ladder (config option + ready-banner gate).
# Emit when rank(wanted) <= rank(configured). Warnings always emit separately.
LOG_LEVEL_WARNING = "warning"
LOG_LEVEL_INFO = "info"
LOG_LEVEL_VERBOSE = "verbose"
LOG_LEVEL_DEBUG = "debug"
LOG_LEVEL_DEFAULT = LOG_LEVEL_INFO
# Rank order (quiet → loud); single source for set + user-facing choices text.
LOG_LEVEL_ORDER = (
    LOG_LEVEL_WARNING,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    LOG_LEVEL_DEBUG,
)
LOG_LEVEL_RANK = {name: i + 1 for i, name in enumerate(LOG_LEVEL_ORDER)}
LOG_LEVELS = frozenset(LOG_LEVEL_ORDER)
LOG_LEVEL_CHOICES = ", ".join(LOG_LEVEL_ORDER)

# Early config validation — severity labels.
CONFIG_SEVERITY_ERROR = "error"

# Host [klipper_extras] keys (docs/sample must stay a subset).
CONFIG_OPTION_KEYS = frozenset(("log_level", "min_nozzle_temp"))

# Extra °C when the heat floor is [extruder] min_extrude_temp (PID undershoot).
# User min_nozzle_temp / nozzle_temperature are not padded.
MIN_EXTRUDE_TEMP_HEAT_MARGIN = 5.0


def heat_floor_from_min_extrude_temp(min_extrude: Optional[float]) -> Optional[float]:
    """Hint floor: live min_extrude_temp plus PID margin, or None."""
    if min_extrude is None:
        return None
    return float(min_extrude) + MIN_EXTRUDE_TEMP_HEAT_MARGIN


def log_level_enabled(configured: str, wanted: str) -> bool:
    """True when *wanted* should emit under configured *log_level*."""
    return LOG_LEVEL_RANK[wanted] <= LOG_LEVEL_RANK[configured]


def ready_lines_for_log_level(
    banner: str,
    detail: list[str],
    log_level: str,
) -> list[str]:
    """Select ready announce lines: banner at info+, detail at verbose+.

    Pure filter — no Klipper. Empty when log_level is warning (or quieter).
    """
    if not log_level_enabled(log_level, LOG_LEVEL_INFO):
        return []
    lines = [banner]
    if log_level_enabled(log_level, LOG_LEVEL_VERBOSE):
        lines.extend(detail)
    return lines
