"""Wipe-motion library strings (% formatting)."""

from __future__ import annotations


def xy_required(kind: str) -> str:
    return (
        "klipper_common: [%s] needs start_x, start_y, end_x, end_y "
        "(no Klipper field for wiper pose)" % (kind,)
    )


def wipe_z_negative() -> str:
    return "klipper_common: wipe_z must be >= 0"


def z_hop_negative() -> str:
    return "klipper_common: z_hop must be >= 0"


def travel_z_too_low() -> str:
    return "klipper_common: travel_z must be greater than wipe_z"


def speed_not_positive(key: str) -> str:
    return "klipper_common: %s must be > 0" % (key,)


def passes_invalid() -> str:
    return "klipper_common: passes must be an integer >= 1"


def fan_speed_invalid() -> str:
    return "klipper_common: fan_speed must be between 0 and 1"


def retract_invalid() -> str:
    return "klipper_common: retract must be >= 0"


def zero_length() -> str:
    return "klipper_common: wipe start and end must not be the same point"


def nozzle_temp_below_min() -> str:
    return "klipper_common: nozzle_temperature must be >= min_nozzle_temp"


def not_homed() -> str:
    return "klipper_common: XYZ must be homed before wipe"


def nozzle_too_cold(current: float, minimum: float) -> str:
    return (
        "klipper_common: nozzle too cold (%.1fC, need >= %.1fC); "
        "heat first or set nozzle_temperature" % (current, minimum)
    )


def no_extruder() -> str:
    return "klipper_common: extruder not found (needed for wipe temperature)"


def fan_missing(name: str) -> str:
    return "klipper_common: fan object %r not found" % (name,)


def not_ready() -> str:
    return "klipper_common: wipe settings not resolved yet"


def skip_nozzle_wait() -> str:
    return (
        "klipper_common: no min_extrude_temp / min_nozzle_temp; "
        "skipping nozzle wait"
    )


def restore_gcode_state_failed(name: str) -> str:
    return "klipper_common: restore gcode state %s failed" % (name,)


def lift_before_restore_failed() -> str:
    return "klipper_common: lift before restore gcode state failed"


def restore_fan_failed() -> str:
    return "klipper_common: restore fan failed"
