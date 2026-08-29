"""Named literals for the wipe-motion library (not host, not per-feature)."""

from __future__ import annotations

MOVE_TRAVEL = "travel"
MOVE_WIPE = "wipe"
MOVE_LIFT = "lift"

DEFAULT_TRAVEL_Z = 5.0
DEFAULT_Z_HOP = 5.0
DEFAULT_TRAVEL_SPEED = 200.0
DEFAULT_PASSES = 4
DEFAULT_RETRACT = 0.5
DEFAULT_RETRACT_SPEED = 5.0
DEFAULT_FAN_SPEED = 1.0
DEFAULT_FAN_OBJECT = "fan"

# Feature G-code wrap. NAME is the feature G-code. MOVE_SPEED is mm/s (Klipper).
CMD_ABSOLUTE = "G90"
CMD_SAVE_GCODE_STATE = "SAVE_GCODE_STATE NAME=%s"
CMD_RESTORE_GCODE_STATE = "RESTORE_GCODE_STATE NAME=%s MOVE=1 MOVE_SPEED=%.0f"
