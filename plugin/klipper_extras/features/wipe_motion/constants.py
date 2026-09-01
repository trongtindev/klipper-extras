"""Named literals for the wipe-motion library (not host, not per-feature)."""

from __future__ import annotations

MOVE_TRAVEL = "travel"
MOVE_WIPE = "wipe"
MOVE_LIFT = "lift"

DEFAULT_TRAVEL_Z = 5.0
DEFAULT_Z_HOP = 5.0
DEFAULT_TRAVEL_SPEED = 200.0
DEFAULT_RETRACT = 0.5
DEFAULT_RETRACT_SPEED = 5.0
DEFAULT_FAN_SPEED = 1.0
DEFAULT_FAN_OBJECT = "fan"

# Command-time pause (pause_resume.is_paused). Set on FeatureSpec.paused_mode.
PAUSED_REFUSE = "refuse"
PAUSED_HOLD_Z_IF_OMITTED = "hold_z_if_omitted"
USER_Z_KEYS = ("wipe_z", "z_hop", "travel_z")

# Feature G-code wrap. NAME is the feature G-code. MOVE is 0|1. MOVE_SPEED is mm/s (Klipper).
CMD_ABSOLUTE = "G90"
CMD_SAVE_GCODE_STATE = "SAVE_GCODE_STATE NAME=%s"
CMD_RESTORE_GCODE_STATE = "RESTORE_GCODE_STATE NAME=%s MOVE=%d MOVE_SPEED=%.0f"
