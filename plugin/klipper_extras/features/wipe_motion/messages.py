"""Wipe-motion library strings (% formatting)."""

from __future__ import annotations

from ... import messages as host_msg

fan_missing = host_msg.fan_missing
fan_speed_invalid = host_msg.fan_speed_invalid
lift_before_restore_failed = host_msg.lift_before_restore_failed
line = host_msg.line
must_be_ge_0 = host_msg.must_be_ge_0
nozzle_temp_below_min = host_msg.nozzle_temp_below_min
nozzle_too_cold = host_msg.nozzle_too_cold
not_allowed_while_paused = host_msg.not_allowed_while_paused
restore_fan_failed = host_msg.restore_fan_failed
restore_gcode_state_failed = host_msg.restore_gcode_state_failed
speed_not_positive = host_msg.must_be_gt_0


def xy_required(kind: str) -> str:
    return host_msg.pose_required(
        kind, "start_x, start_y, end_x, end_y", "wiper pose"
    )


def wipe_z_negative() -> str:
    return must_be_ge_0("wipe_z")


def z_hop_negative() -> str:
    return must_be_ge_0("z_hop")


def travel_z_too_low() -> str:
    return line("travel_z must be greater than wipe_z")


def passes_invalid() -> str:
    return line("passes must be an integer >= 1")


def retract_invalid() -> str:
    return must_be_ge_0("retract")


def zero_length() -> str:
    return line("wipe start and end must not be the same point")


def not_homed() -> str:
    return line("XYZ must be homed before wipe")


def not_allowed_while_paused_with_z(gcode_name: str, z_keys) -> str:
    return line(
        "%s is not allowed while paused with %s set "
        "(omit wipe_z, z_hop, travel_z to wipe XY at current Z, or resume)",
        gcode_name,
        ", ".join(z_keys),
    )


def no_extruder() -> str:
    return line("extruder not found (needed for wipe temperature)")


def not_ready() -> str:
    return line("wipe settings not resolved yet")


def skip_nozzle_wait() -> str:
    return line("no min_extrude_temp / min_nozzle_temp; skipping nozzle wait")
