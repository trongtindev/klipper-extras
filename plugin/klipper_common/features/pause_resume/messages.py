"""User-facing strings for pause_resume (% formatting)."""

from __future__ import annotations


def help_pause() -> str:
    return "Pause the print (requires [klipper_common pause_resume])"


def help_resume() -> str:
    return "Resume the print (requires [klipper_common pause_resume])"


def help_cancel_print() -> str:
    return "Cancel the print (requires [klipper_common pause_resume])"


def not_ready() -> str:
    return "klipper_common: pause_resume is not ready"


def already_paused() -> str:
    return "Print already paused"


def not_paused() -> str:
    return "Print is not paused, resume aborted"


def not_printing() -> str:
    return "Print is not active, pause aborted"


def not_cancelling() -> str:
    return "Print is not active, cancel aborted"


def park_pair_required(x_key: str, y_key: str) -> str:
    return "klipper_common: %s and %s must both be set or both omitted" % (
        x_key,
        y_key,
    )


def speed_not_positive(key: str) -> str:
    return "klipper_common: %s must be > 0" % (key,)


def length_invalid(key: str) -> str:
    return "klipper_common: %s must be >= 0" % (key,)


def z_hop_negative() -> str:
    return "klipper_common: z_hop must be >= 0"


def idle_timeout_invalid() -> str:
    return "klipper_common: idle_timeout must be >= 0"


def z_park_too_high(needed: float, maximum: float) -> str:
    return "klipper_common: z park %.3f mm exceeds axis maximum %.3f mm" % (
        needed,
        maximum,
    )


def not_homed_skip(action: str) -> str:
    return "klipper_common: skip %s (axes not homed)" % (action,)


def retract_skipped_cold() -> str:
    return "klipper_common: skip retract (extruder not hot enough)"


def resume_aborted_title() -> str:
    return "RESUME aborted"


def resume_cold_text() -> str:
    return "Extruder not hot enough. Heat, then press RESUME."


def resume_runout_text(sensor: str) -> str:
    return "No filament on %s. Load filament, then press RESUME." % (sensor,)


def prompt_ok() -> str:
    return "Ok"


def park_at_cancel_no_xy() -> str:
    return (
        "klipper_common: park_at_cancel is true but no park XY "
        "(set park_x/park_y or cancel_park_x/cancel_park_y)"
    )
