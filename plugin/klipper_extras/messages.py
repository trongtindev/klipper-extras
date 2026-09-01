"""User-facing and log strings for klipper_extras host (% formatting)."""

from __future__ import annotations

from typing import Optional

from .constants import (
    EXTRA_NAME,
    KLIPPER_EXTRAS_VERSION,
    LOG_LEVEL_CHOICES,
    extra_object,
)
from .klipper_version import VersionTuple, format_version_tuple


def extra_section(kind: Optional[str] = None) -> str:
    """Config section: ``[klipper_extras]`` or ``[klipper_extras kind]``."""
    return "[%s]" % (extra_object(kind),)


def line(fmt: str, *args) -> str:
    """One console/log sentence: extra name, colon, formatted body."""
    body = fmt % args if args else fmt
    return "%s: %s" % (EXTRA_NAME, body)


def pose_required(kind: str, keys: str, what: str) -> str:
    """Missing user pose keys (no Klipper field to invent them from)."""
    return line(
        "[%s] needs %s (no Klipper field for %s)",
        kind,
        keys,
        what,
    )


def must_be_gt_0(key: str) -> str:
    return line("%s must be > 0", key)


def must_be_ge_0(key: str) -> str:
    return line("%s must be >= 0", key)


def fan_speed_invalid() -> str:
    return line("fan_speed must be between 0 and 1")


def nozzle_temp_below_min() -> str:
    return line("nozzle_temperature must be >= min_nozzle_temp")


def fan_missing(name: str) -> str:
    return line("fan object %r not found", name)


def restore_gcode_state_failed(name: str) -> str:
    return line("restore gcode state %s failed", name)


def restore_fan_failed() -> str:
    return line("restore fan failed")


def lift_before_restore_failed() -> str:
    return line("lift before restore gcode state failed")


def not_allowed_while_paused(gcode_name: str) -> str:
    return line("%s is not allowed while paused", gcode_name)


def nozzle_too_cold(current: float, minimum: float) -> str:
    return line(
        "nozzle too cold (%.1fC, need >= %.1fC); "
        "heat first or set nozzle_temperature",
        current,
        minimum,
    )


def ready_banner(version: str = KLIPPER_EXTRAS_VERSION) -> str:
    return "%s v%s ready" % (EXTRA_NAME, version)


def ready_detail_lines(
    log_level: str, extra_gcodes: Optional[list[str]] = None
) -> list[str]:
    names = ["EXTRAS_STATUS", "EXTRAS_VERSION"]
    if extra_gcodes:
        names.extend(extra_gcodes)
    return [
        line("log_level=%s", log_level),
        line("gcodes %s", ", ".join(names)),
    ]


def config_warnings_ready_note(count: int) -> str:
    return line("%d config warning(s) — see klippy.log", count)


def klipper_version_too_old(found, required: VersionTuple) -> str:
    return line(
        "Klipper %s is too old (need >= v%s)",
        found,
        format_version_tuple(required),
    )


def klipper_version_unparseable(found, required: VersionTuple) -> str:
    return line(
        "cannot parse Klipper version %r (need >= v%s)",
        found,
        format_version_tuple(required),
    )


def invalid_log_level(value: str) -> str:
    return line("invalid log_level %r (choices: %s)", value, LOG_LEVEL_CHOICES)


def invalid_number(key: str, value) -> str:
    return line("invalid %s %r (need a number)", key, value)


def invalid_int(key: str, value) -> str:
    return line("invalid %s %r (need an integer)", key, value)


def invalid_min_nozzle_temp(value) -> str:
    return invalid_number("min_nozzle_temp", value)


def config_validation_failed(errors: list[str]) -> str:
    return line("config invalid:\n  %s", "\n  ".join(errors))


def log_config_ok(plugin_version: str, klipper_version: str, log_level: str) -> str:
    return "%s v%s loaded (Klipper %s, log_level=%s)" % (
        EXTRA_NAME,
        plugin_version,
        klipper_version,
        log_level,
    )


def status_report(
    plugin_version: str,
    klipper_version: str,
    log_level: str,
    extra_gcodes: Optional[list[str]] = None,
) -> str:
    text = line(
        "version=%s klipper=%s log_level=%s",
        plugin_version,
        klipper_version,
        log_level,
    )
    if extra_gcodes:
        text += " gcodes=%s" % (",".join(extra_gcodes),)
    return text


def version_report(plugin_version: str) -> str:
    return "%s %s" % (EXTRA_NAME, plugin_version)


def help_extras_status() -> str:
    return "Report %s version, Klipper version, and log_level" % (EXTRA_NAME,)


def help_extras_version() -> str:
    return "Report %s plugin version" % (EXTRA_NAME,)


def unknown_feature_prefix(name: str) -> str:
    return line("unknown feature section %s", extra_section(name))


def feature_requires_host(kind: str) -> str:
    return line("%s is required to enable [%s]", extra_section(), kind)


def invalid_bool(key: str, value) -> str:
    return line("invalid %s %r (need true/false or 0/1)", key, value)


def components_required_missing(kind: str, names) -> str:
    return line("[%s] requires Klipper extra(s) %s (missing)", kind, ", ".join(names))


def component_optional_missing(kind: str, name: str) -> str:
    return line("[%s] optional extra %s is not loaded", kind, name)
