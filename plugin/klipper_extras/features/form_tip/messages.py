"""User-facing strings for form_tip (% formatting)."""

from __future__ import annotations

from ... import messages as host_msg

extra_section = host_msg.extra_section
fan_missing = host_msg.fan_missing
fan_speed_invalid = host_msg.fan_speed_invalid
invalid_bool = host_msg.invalid_bool
line = host_msg.line
must_be_ge_0 = host_msg.must_be_ge_0
nozzle_temp_below_min = host_msg.nozzle_temp_below_min
nozzle_too_cold = host_msg.nozzle_too_cold
restore_fan_failed = host_msg.restore_fan_failed
restore_gcode_state_failed = host_msg.restore_gcode_state_failed
speed_not_positive = host_msg.must_be_gt_0


def help_form_tip() -> str:
    return "Form filament tip before unload (requires %s)" % (
        extra_section("form_tip"),
    )


def length_invalid(key: str, value) -> str:
    return line("%s must be >= 0, got %r", key, value)


def unknown_profile(name: str, known: str) -> str:
    return line("unknown profile %r (known: %s)", name, known)


def tip_distance_required() -> str:
    return line("tip_distance is required (set in profile or section)")


def sep_too_long(sep_fast: float, unload_start: float, tip_dist: float) -> str:
    return line(
        "sep_fast_len (%.1f) + unloading_speed_start_len (%.1f) "
        "= %.1f > tip_distance (%.1f)",
        sep_fast,
        unload_start,
        sep_fast + unload_start,
        tip_dist,
    )


def cooling_moves_invalid() -> str:
    return must_be_ge_0("cooling_moves")


def cool_len_needed() -> str:
    return line("cool_len must be > 0 when cooling_moves > 0")


def dip_in_needed() -> str:
    return line("dip_in must be > 0 when use_skinnydip is true")


def not_ready() -> str:
    return line("form_tip settings not resolved yet")


def skip_nozzle_wait() -> str:
    return line("no min_nozzle_temp / nozzle_temperature; skipping nozzle wait")


def no_extruder() -> str:
    return line("extruder not found (needed for tip temperature)")
