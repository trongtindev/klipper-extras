"""User-facing strings for form_tip (% formatting)."""

from __future__ import annotations


def help_form_tip() -> str:
    return "Form filament tip before unload (requires [klipper_common form_tip])"


def speed_not_positive(key: str) -> str:
    return "klipper_common: %s must be > 0" % (key,)


def length_invalid(key: str, value) -> str:
    return "klipper_common: %s must be >= 0, got %r" % (key, value)


def invalid_bool(key: str, value) -> str:
    return "klipper_common: invalid %s %r (need true/false or 0/1)" % (key, value)


def unknown_profile(name: str, known: str) -> str:
    return "klipper_common: unknown profile %r (known: %s)" % (name, known)


def tip_distance_required() -> str:
    return "klipper_common: tip_distance is required (set in profile or section)"


def sep_too_long(sep_fast: float, unload_start: float, tip_dist: float) -> str:
    return (
        "klipper_common: sep_fast_len (%.1f) + unloading_speed_start_len (%.1f) "
        "= %.1f > tip_distance (%.1f)" % (sep_fast, unload_start, sep_fast + unload_start, tip_dist)
    )


def cooling_moves_invalid() -> str:
    return "klipper_common: cooling_moves must be >= 0"


def cool_len_needed() -> str:
    return "klipper_common: cool_len must be > 0 when cooling_moves > 0"


def dip_in_needed() -> str:
    return "klipper_common: dip_in must be > 0 when use_skinnydip is true"


def fan_speed_invalid() -> str:
    return "klipper_common: fan_speed must be between 0 and 1"


def nozzle_temp_below_min() -> str:
    return "klipper_common: nozzle_temperature must be >= min_nozzle_temp"


def fan_missing(name: str) -> str:
    return "klipper_common: fan object %r not found" % (name,)


def not_ready() -> str:
    return "klipper_common: form_tip settings not resolved yet"


def skip_nozzle_wait() -> str:
    return (
        "klipper_common: no min_nozzle_temp / nozzle_temperature; "
        "skipping nozzle wait"
    )


def no_extruder() -> str:
    return "klipper_common: extruder not found (needed for tip temperature)"


def nozzle_too_cold(current: float, minimum: float) -> str:
    return (
        "klipper_common: nozzle too cold (%.1fC, need >= %.1fC); "
        "heat first or set nozzle_temperature" % (current, minimum)
    )


def restore_gcode_state_failed(name: str) -> str:
    return "klipper_common: restore gcode state %s failed" % (name,)


def restore_fan_failed() -> str:
    return "klipper_common: restore fan failed"
