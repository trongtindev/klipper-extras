"""Owned keys and safe defaults for wipe-nozzle-on-rubber."""

from __future__ import annotations

from ..wipe_motion.constants import (
    DEFAULT_FAN_SPEED,
    DEFAULT_RETRACT,
    DEFAULT_RETRACT_SPEED,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_TRAVEL_Z,
    PAUSED_HOLD_Z_IF_OMITTED,
    wipe_hook_option_keys,
)
from ..wipe_motion.types import FeatureSpec, WipeKindProfile
from .messages import help_wipe_rubber

KIND = "wipe_nozzle_on_rubber"
GCODE = "WIPE_NOZZLE_ON_RUBBER"

DEFAULT_WIPE_Z = 0.0
DEFAULT_WIPE_SPEED = 50.0
DEFAULT_PASSES = 2
DEFAULT_PASS_OFFSET = 0.0

# Rubber-owned keys. Pad pose is this section's box; not inferred from Klipper.
OPTION_KEYS = frozenset(
    (
        "start_x",
        "start_y",
        "end_x",
        "end_y",
        "wipe_z",
        "z_hop",
        "travel_z",
        "wipe_speed",
        "travel_speed",
        "passes",
        "pass_offset",
        "retract",
        "retract_speed",
        "min_nozzle_temp",
        "nozzle_temperature",
        "fan_speed",
        "fan",
    )
) | wipe_hook_option_keys()

PROFILE = WipeKindProfile(
    wipe_z=DEFAULT_WIPE_Z,
    travel_z=DEFAULT_TRAVEL_Z,
    wipe_speed=DEFAULT_WIPE_SPEED,
    travel_speed=DEFAULT_TRAVEL_SPEED,
    passes=DEFAULT_PASSES,
    pass_offset=DEFAULT_PASS_OFFSET,
    retract=DEFAULT_RETRACT,
    retract_speed=DEFAULT_RETRACT_SPEED,
    fan_speed=DEFAULT_FAN_SPEED,
)

SPEC = FeatureSpec(
    kind=KIND,
    gcode=GCODE,
    option_keys=OPTION_KEYS,
    help_text=help_wipe_rubber(),
    derive_xy=False,
    profile=PROFILE,
    paused_mode=PAUSED_HOLD_Z_IF_OMITTED,
)
