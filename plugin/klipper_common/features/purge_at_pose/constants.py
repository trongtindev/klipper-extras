"""Owned keys and safe defaults for purge-at-pose."""

from __future__ import annotations

from ..purge_motion.constants import (
    DEFAULT_FAN_SPEED,
    DEFAULT_FLOW_RATE,
    DEFAULT_POSE_PURGE_AMOUNT,
    DEFAULT_RETRACT,
    DEFAULT_RETRACT_SPEED,
    DEFAULT_TIP_DISTANCE,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_TRAVEL_Z,
    PAUSED_HOLD_Z,
    SHARED_OPTION_KEYS,
)
from ..purge_motion.types import FeatureSpec, PurgeKindProfile
from .messages import help_purge_pose

KIND = "purge_at_pose"
GCODE = "PURGE_AT_POSE"

OPTION_KEYS = SHARED_OPTION_KEYS

PROFILE = PurgeKindProfile(
    purge_amount=DEFAULT_POSE_PURGE_AMOUNT,
    flow_rate=DEFAULT_FLOW_RATE,
    travel_z=DEFAULT_TRAVEL_Z,
    travel_speed=DEFAULT_TRAVEL_SPEED,
    retract=DEFAULT_RETRACT,
    retract_speed=DEFAULT_RETRACT_SPEED,
    fan_speed=DEFAULT_FAN_SPEED,
    tip_distance=DEFAULT_TIP_DISTANCE,
    purge_z=None,
)

SPEC = FeatureSpec(
    kind=KIND,
    gcode=GCODE,
    option_keys=OPTION_KEYS,
    help_text=help_purge_pose(),
    move_while_purge=False,
    require_pose=True,
    profile=PROFILE,
    paused_mode=PAUSED_HOLD_Z,
)
