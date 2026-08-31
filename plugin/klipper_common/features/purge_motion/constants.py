"""Named literals for the purge-motion library (not host, not per-feature)."""

from __future__ import annotations

from ..hook.policy import hook_option_keys_for_actions

MOVE_TRAVEL = "travel"
MOVE_PURGE = "purge"
MOVE_LIFT = "lift"

STYLE_LINE = "line"
STYLE_VORON = "voron"
BED_STYLES = frozenset((STYLE_LINE, STYLE_VORON))

ALONG_X = "x"
ALONG_Y = "y"
ALONG_CHOICES = frozenset((ALONG_X, ALONG_Y))

ORIGIN_FIXED = "fixed"
ORIGIN_ADAPTIVE = "adaptive"

DEFAULT_TRAVEL_Z = 5.0
DEFAULT_Z_HOP = 5.0
DEFAULT_TRAVEL_SPEED = 200.0
DEFAULT_RETRACT = 0.5
DEFAULT_RETRACT_SPEED = 5.0
DEFAULT_FAN_SPEED = 1.0
DEFAULT_FAN_OBJECT = "fan"
DEFAULT_FLOW_RATE = 12.0
DEFAULT_TIP_DISTANCE = 0.0
DEFAULT_PURGE_MARGIN = 10.0
DEFAULT_STYLE_SIZE = 10.0
DEFAULT_BED_PURGE_Z = 0.8
DEFAULT_BED_PURGE_AMOUNT = 30.0
DEFAULT_POSE_PURGE_AMOUNT = 10.0
BREAK_TRAVEL = 10.0

# Named purge actions. Each has before_<name>_gcode / after_<name>_gcode.
PURGE_HOOK_ACTIONS = (
    "heat",
    "tip",
    "fan",
    "z_hop",
    "travel",
    "lower",
    "purge",
    "retract",
    "recover",
    "break",
    "lift",
)


def purge_hook_option_keys():
    """Keys owned on each purge feature section (not imported from hook.OPTION_KEYS)."""
    return hook_option_keys_for_actions(PURGE_HOOK_ACTIONS)


SHARED_OPTION_KEYS = frozenset(
    (
        "purge_amount",
        "flow_rate",
        "tip_distance",
        "purge_z",
        "travel_z",
        "z_hop",
        "travel_speed",
        "retract",
        "retract_speed",
        "min_nozzle_temp",
        "nozzle_temperature",
        "fan_speed",
        "fan",
        "start_x",
        "start_y",
    )
) | purge_hook_option_keys()

CMD_ABSOLUTE = "G90"
CMD_EXTRUDE_REL = "M83"
CMD_SAVE_GCODE_STATE = "SAVE_GCODE_STATE NAME=%s"
CMD_RESTORE_GCODE_STATE = "RESTORE_GCODE_STATE NAME=%s MOVE=1 MOVE_SPEED=%.0f"

# Klipper extras (object name, G-code). Warn at purge if loaded and not applied.
LEVELING_OBJECT_COMMANDS = (
    ("quad_gantry_level", "QUAD_GANTRY_LEVEL"),
    ("z_tilt", "Z_TILT_ADJUST"),
)
