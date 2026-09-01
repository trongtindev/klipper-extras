"""User-facing strings for pause_resume (% formatting)."""

from __future__ import annotations

from ... import messages as host_msg

extra_section = host_msg.extra_section
line = host_msg.line
must_be_ge_0 = host_msg.must_be_ge_0
speed_not_positive = host_msg.must_be_gt_0


def help_pause() -> str:
    return "Pause the print (requires %s)" % (extra_section("pause_resume"),)


def help_resume() -> str:
    return "Resume the print (requires %s)" % (extra_section("pause_resume"),)


def help_cancel_print() -> str:
    return "Cancel the print (requires %s)" % (extra_section("pause_resume"),)


def not_ready() -> str:
    return line("pause_resume is not ready")


def already_paused() -> str:
    return "Print already paused"


def not_paused() -> str:
    return "Print is not paused, resume aborted"


def not_printing() -> str:
    return "Print is not active, pause aborted"


def not_cancelling() -> str:
    return "Print is not active, cancel aborted"


def park_pair_required(x_key: str, y_key: str) -> str:
    return line("%s and %s must both be set or both omitted", x_key, y_key)


def length_invalid(key: str) -> str:
    return must_be_ge_0(key)


def z_hop_negative() -> str:
    return must_be_ge_0("z_hop")


def idle_timeout_invalid() -> str:
    return must_be_ge_0("idle_timeout")


def z_park_too_high(needed: float, maximum: float) -> str:
    return line("z park %.3f mm exceeds axis maximum %.3f mm", needed, maximum)


def not_homed_skip(action: str) -> str:
    return line("skip %s (axes not homed)", action)


def retract_skipped_cold() -> str:
    return line("skip retract (extruder not hot enough)")


def resume_aborted_title() -> str:
    return "RESUME aborted"


def resume_cold_text() -> str:
    return "Extruder not hot enough. Heat, then press RESUME."


def resume_runout_text(sensor: str) -> str:
    return "No filament on %s. Load filament, then press RESUME." % (sensor,)


def prompt_ok() -> str:
    return "Ok"


def park_at_cancel_no_xy() -> str:
    return line(
        "park_at_cancel is true but no park XY "
        "(set park_x/park_y or cancel_park_x/cancel_park_y)"
    )
