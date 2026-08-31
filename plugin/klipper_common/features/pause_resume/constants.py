"""Owned keys and literals for pause_resume."""

from __future__ import annotations

from ..hook.policy import hook_option_keys_for_actions
from .messages import help_cancel_print, help_pause, help_resume

KIND = "pause_resume"
GCODE = "PAUSE"
GCODES = ("PAUSE", "RESUME", "CANCEL_PRINT")

REQUIRED_COMPONENTS = ("virtual_sdcard", "pause_resume", "respond")

# print_stats.get_status()["state"] (extras/print_stats.py)
PRINT_STATE_PRINTING = "printing"
PRINT_STATE_PAUSED = "paused"

PAUSE_RESUME_HOOK_ACTIONS = (
    "pause",
    "resume",
    "cancel",
)

DEFAULT_Z_HOP = 5.0
DEFAULT_TRAVEL_SPEED = 200.0
DEFAULT_RETRACT = 0.5
DEFAULT_RETRACT_SPEED = 5.0
DEFAULT_CANCEL_RETRACT = 5.0
DEFAULT_PARK_AT_CANCEL = False
DEFAULT_RESTORE_TEMPERATURE = True
DEFAULT_IDLE_TIMEOUT = 0.0

HELP_PAUSE = help_pause()
HELP_RESUME = help_resume()
HELP_CANCEL = help_cancel_print()

OPTION_KEYS = frozenset(
    (
        "park_x",
        "park_y",
        "z_hop",
        "travel_speed",
        "z_speed",
        "retract",
        "retract_speed",
        "unretract",
        "unretract_speed",
        "cancel_retract",
        "park_at_cancel",
        "cancel_park_x",
        "cancel_park_y",
        "idle_timeout",
        "restore_temperature",
        "runout_sensor",
    )
) | hook_option_keys_for_actions(PAUSE_RESUME_HOOK_ACTIONS)
