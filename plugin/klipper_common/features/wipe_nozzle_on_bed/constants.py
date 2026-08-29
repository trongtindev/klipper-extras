"""Owned keys and safe defaults for wipe-nozzle-on-bed."""

from __future__ import annotations

from ..wipe_motion.constants import (
    DEFAULT_FAN_SPEED,
    DEFAULT_PASSES,
    DEFAULT_RETRACT,
    DEFAULT_RETRACT_SPEED,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_TRAVEL_Z,
)
from ..wipe_motion.types import FeatureSpec, WipeKindProfile
from .messages import help_wipe_bed

KIND = "wipe_nozzle_on_bed"
GCODE = "WIPE_NOZZLE_ON_BED"

DEFAULT_WIPE_Z = 0.1
DEFAULT_WIPE_SPEED = 80.0
DEFAULT_PASS_OFFSET = 1.0
DEFAULT_START_X = 50.0
DEFAULT_START_Y = 50.0
DEFAULT_STRIP_LENGTH = 50.0

# Bed-owned keys (this section only). Rubber has its own frozenset.
OPTION_KEYS = frozenset(
    (
        "start_x",
        "start_y",
        "wipe_length",
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
)

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
    wipe_length=DEFAULT_STRIP_LENGTH,
    start_x=DEFAULT_START_X,
    start_y=DEFAULT_START_Y,
)

SPEC = FeatureSpec(
    kind=KIND,
    gcode=GCODE,
    option_keys=OPTION_KEYS,
    help_text=help_wipe_bed(),
    derive_xy=True,
    profile=PROFILE,
)
