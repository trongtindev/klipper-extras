"""Purge-motion library strings (% formatting)."""

from __future__ import annotations

from ... import messages as host_msg

extra_section = host_msg.extra_section
fan_missing = host_msg.fan_missing
fan_speed_invalid = host_msg.fan_speed_invalid
lift_before_restore_failed = host_msg.lift_before_restore_failed
line = host_msg.line
must_be_ge_0 = host_msg.must_be_ge_0
must_be_gt_0 = host_msg.must_be_gt_0
nozzle_temp_below_min = host_msg.nozzle_temp_below_min
not_allowed_while_paused = host_msg.not_allowed_while_paused
restore_fan_failed = host_msg.restore_fan_failed
restore_gcode_state_failed = host_msg.restore_gcode_state_failed
speed_not_positive = host_msg.must_be_gt_0


def pose_required(kind: str) -> str:
    return host_msg.pose_required(kind, "start_x, start_y, purge_z", "purge pose")


def xy_partial() -> str:
    return line("set both start_x and start_y, or omit both (adaptive)")


def unknown_style(name: str, known: str) -> str:
    return line("unknown style %r (known: %s)", name, known)


def unknown_along(name: str) -> str:
    return line("along must be x or y, got %r", name)


def style_key_conflict(key: str, style: str) -> str:
    return line("%s is not valid with style %s", key, style)


def purge_z_required(kind: str) -> str:
    return line("[%s] needs purge_z", kind)


def purge_z_negative() -> str:
    return must_be_ge_0("purge_z")


def z_hop_negative() -> str:
    return must_be_ge_0("z_hop")


def travel_z_too_low() -> str:
    return line("travel_z must be greater than purge_z")


def amount_not_positive() -> str:
    return must_be_gt_0("purge_amount")


def length_not_positive() -> str:
    return must_be_gt_0("purge_length")


def style_size_not_positive() -> str:
    return must_be_gt_0("style_size")


def retract_invalid() -> str:
    return must_be_ge_0("retract")


def tip_distance_invalid() -> str:
    return must_be_ge_0("tip_distance")


def heat_temp_required(kind: str) -> str:
    return line(
        "[%s] needs a nozzle temperature "
        "(set min_nozzle_temp on this section or %s, "
        "min_extrude_temp on [extruder], or nozzle_temperature on this section)",
        kind,
        extra_section(),
    )


def filament_diameter_required() -> str:
    return line("filament_diameter is required (from [extruder] filament_diameter)")


def filament_diameter_invalid() -> str:
    return must_be_gt_0("filament_diameter")


def adaptive_needs_objects() -> str:
    return line("purge_on_bed needs exclude_object objects or start_x and start_y")


def origin_not_resolved() -> str:
    return line("purge origin is not resolved")


def out_of_range(axis: str, current: float, needed: float) -> str:
    return line("%s is %.3f, need %.3f (inside axis range)", axis, current, needed)


def cross_section_too_small(current: float, needed: float) -> str:
    return line(
        "max_extrude_cross_section is %.3f mm2, need >= %.3f mm2",
        current,
        needed,
    )


def not_homed() -> str:
    return line("XYZ must be homed before purge")


def leveling_not_applied(command: str) -> str:
    return line("%s has not been applied", command)


def no_extruder() -> str:
    return line("extruder not found (needed for purge temperature)")


def not_ready() -> str:
    return line("purge settings not resolved yet")
