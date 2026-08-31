"""User-facing and log strings for klipper_common host (% formatting)."""

from __future__ import annotations

from typing import Optional

from .constants import KLIPPER_COMMON_VERSION, LOG_LEVEL_CHOICES
from .klipper_version import VersionTuple, format_version_tuple


def ready_banner(version: str = KLIPPER_COMMON_VERSION) -> str:
    return "klipper_common v%s ready" % (version,)


def ready_detail_lines(
    log_level: str, extra_gcodes: Optional[list[str]] = None
) -> list[str]:
    names = ["COMMON_STATUS", "COMMON_VERSION"]
    if extra_gcodes:
        names.extend(extra_gcodes)
    return [
        "klipper_common: log_level=%s" % (log_level,),
        "klipper_common: gcodes %s" % (", ".join(names),),
    ]


def config_warnings_ready_note(count: int) -> str:
    return "klipper_common: %d config warning(s) — see klippy.log" % (count,)


def klipper_version_too_old(found, required: VersionTuple) -> str:
    return "klipper_common: Klipper %s is too old (need >= v%s)" % (
        found,
        format_version_tuple(required),
    )


def klipper_version_unparseable(found, required: VersionTuple) -> str:
    return "klipper_common: cannot parse Klipper version %r (need >= v%s)" % (
        found,
        format_version_tuple(required),
    )


def invalid_log_level(value: str) -> str:
    return "klipper_common: invalid log_level %r (choices: %s)" % (
        value,
        LOG_LEVEL_CHOICES,
    )


def invalid_number(key: str, value) -> str:
    return "klipper_common: invalid %s %r (need a number)" % (key, value)


def invalid_int(key: str, value) -> str:
    return "klipper_common: invalid %s %r (need an integer)" % (key, value)


def invalid_min_nozzle_temp(value) -> str:
    return "klipper_common: invalid min_nozzle_temp %r (need a number)" % (value,)


def config_validation_failed(errors: list[str]) -> str:
    return "klipper_common: config invalid:\n  %s" % ("\n  ".join(errors),)


def log_config_ok(plugin_version: str, klipper_version: str, log_level: str) -> str:
    return "klipper_common v%s loaded (Klipper %s, log_level=%s)" % (
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
    text = "klipper_common: version=%s klipper=%s log_level=%s" % (
        plugin_version,
        klipper_version,
        log_level,
    )
    if extra_gcodes:
        text += " gcodes=%s" % (",".join(extra_gcodes),)
    return text


def version_report(plugin_version: str) -> str:
    return "klipper_common %s" % (plugin_version,)


def help_common_status() -> str:
    return "Report klipper_common version, Klipper version, and log_level"


def help_common_version() -> str:
    return "Report klipper_common plugin version"


def unknown_feature_prefix(name: str) -> str:
    return "klipper_common: unknown feature section [klipper_common %s]" % (name,)


def feature_requires_host(kind: str) -> str:
    return "klipper_common: [klipper_common] is required to enable [%s]" % (kind,)


def invalid_bool(key: str, value) -> str:
    return "klipper_common: invalid %s %r (need true/false or 0/1)" % (key, value)


def components_required_missing(kind: str, names) -> str:
    return "klipper_common: [%s] requires Klipper extra(s) %s (missing)" % (
        kind,
        ", ".join(names),
    )


def component_optional_missing(kind: str, name: str) -> str:
    return "klipper_common: [%s] optional extra %s is not loaded" % (kind, name)
