"""Owned keys and safe defaults for purge-on-bed."""

from __future__ import annotations

from ..purge_motion.constants import (
    DEFAULT_BED_PURGE_AMOUNT,
    DEFAULT_BED_PURGE_Z,
    DEFAULT_FAN_SPEED,
    DEFAULT_FLOW_RATE,
    DEFAULT_PURGE_MARGIN,
    DEFAULT_RETRACT,
    DEFAULT_RETRACT_SPEED,
    DEFAULT_STYLE_SIZE,
    DEFAULT_TIP_DISTANCE,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_TRAVEL_Z,
    SHARED_OPTION_KEYS,
    STYLE_LINE,
)
from ..purge_motion.types import FeatureSpec, PurgeKindProfile
from .messages import help_purge_bed

KIND = "purge_on_bed"
GCODE = "PURGE_ON_BED"

OPTION_KEYS = SHARED_OPTION_KEYS | frozenset(
    (
        "style",
        "purge_length",
        "purge_margin",
        "along",
        "style_size",
    )
)

PROFILE = PurgeKindProfile(
    purge_amount=DEFAULT_BED_PURGE_AMOUNT,
    flow_rate=DEFAULT_FLOW_RATE,
    travel_z=DEFAULT_TRAVEL_Z,
    travel_speed=DEFAULT_TRAVEL_SPEED,
    retract=DEFAULT_RETRACT,
    retract_speed=DEFAULT_RETRACT_SPEED,
    fan_speed=DEFAULT_FAN_SPEED,
    tip_distance=DEFAULT_TIP_DISTANCE,
    purge_z=DEFAULT_BED_PURGE_Z,
    style=STYLE_LINE,
    along="x",
    style_size=DEFAULT_STYLE_SIZE,
    purge_margin=DEFAULT_PURGE_MARGIN,
)

SPEC = FeatureSpec(
    kind=KIND,
    gcode=GCODE,
    option_keys=OPTION_KEYS,
    help_text=help_purge_bed(),
    move_while_purge=True,
    require_pose=False,
    profile=PROFILE,
)
