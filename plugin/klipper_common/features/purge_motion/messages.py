"""Purge-motion library strings (% formatting)."""

from __future__ import annotations


def pose_required(kind: str) -> str:
    return (
        "klipper_common: [%s] needs start_x, start_y, purge_z "
        "(no Klipper field for purge pose)" % (kind,)
    )


def xy_partial() -> str:
    return "klipper_common: set both start_x and start_y, or omit both (adaptive)"


def unknown_style(name: str, known: str) -> str:
    return "klipper_common: unknown style %r (known: %s)" % (name, known)


def unknown_along(name: str) -> str:
    return "klipper_common: along must be x or y, got %r" % (name,)


def style_key_conflict(key: str, style: str) -> str:
    return "klipper_common: %s is not valid with style %s" % (key, style)


def purge_z_required(kind: str) -> str:
    return "klipper_common: [%s] needs purge_z" % (kind,)


def purge_z_negative() -> str:
    return "klipper_common: purge_z must be >= 0"


def z_hop_negative() -> str:
    return "klipper_common: z_hop must be >= 0"


def travel_z_too_low() -> str:
    return "klipper_common: travel_z must be greater than purge_z"


def speed_not_positive(key: str) -> str:
    return "klipper_common: %s must be > 0" % (key,)


def amount_not_positive() -> str:
    return "klipper_common: purge_amount must be > 0"


def length_not_positive() -> str:
    return "klipper_common: purge_length must be > 0"


def style_size_not_positive() -> str:
    return "klipper_common: style_size must be > 0"


def fan_speed_invalid() -> str:
    return "klipper_common: fan_speed must be between 0 and 1"


def retract_invalid() -> str:
    return "klipper_common: retract must be >= 0"


def tip_distance_invalid() -> str:
    return "klipper_common: tip_distance must be >= 0"


def nozzle_temp_below_min() -> str:
    return "klipper_common: nozzle_temperature must be >= min_nozzle_temp"


def heat_temp_required(kind: str) -> str:
    return (
        "klipper_common: [%s] needs a nozzle temperature "
        "(set min_nozzle_temp on this section or [klipper_common], "
        "min_extrude_temp on [extruder], or nozzle_temperature on this section)"
        % (kind,)
    )


def filament_diameter_required() -> str:
    return (
        "klipper_common: filament_diameter is required "
        "(from [extruder] filament_diameter)"
    )


def filament_diameter_invalid() -> str:
    return "klipper_common: filament_diameter must be > 0"


def adaptive_needs_objects() -> str:
    return (
        "klipper_common: purge_on_bed needs exclude_object objects "
        "or start_x and start_y"
    )


def origin_not_resolved() -> str:
    return "klipper_common: purge origin is not resolved"


def out_of_range(axis: str, current: float, needed: float) -> str:
    return (
        "klipper_common: %s is %.3f, need %.3f (inside axis range)"
        % (axis, current, needed)
    )


def cross_section_too_small(current: float, needed: float) -> str:
    return (
        "klipper_common: max_extrude_cross_section is %.3f mm2, need >= %.3f mm2"
        % (current, needed)
    )


def not_homed() -> str:
    return "klipper_common: XYZ must be homed before purge"


def leveling_not_applied(command: str) -> str:
    return "klipper_common: %s has not been applied" % (command,)


def no_extruder() -> str:
    return "klipper_common: extruder not found (needed for purge temperature)"


def fan_missing(name: str) -> str:
    return "klipper_common: fan object %r not found" % (name,)


def not_ready() -> str:
    return "klipper_common: purge settings not resolved yet"


def restore_gcode_state_failed(name: str) -> str:
    return "klipper_common: restore gcode state %s failed" % (name,)


def lift_before_restore_failed() -> str:
    return "klipper_common: lift before restore gcode state failed"


def restore_fan_failed() -> str:
    return "klipper_common: restore fan failed"
