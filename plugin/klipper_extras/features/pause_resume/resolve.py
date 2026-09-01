"""Resolve pause_resume settings (pure)."""

from __future__ import annotations

from typing import Optional

from ...resolve import (
    as_float,
    pick_bool,
    pick_float,
    pick_optional_str,
    pick_speed,
    present,
)
from .constants import (
    DEFAULT_CANCEL_RETRACT,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_PARK_AT_CANCEL,
    DEFAULT_RESTORE_TEMPERATURE,
    DEFAULT_RETRACT,
    DEFAULT_RETRACT_SPEED,
    DEFAULT_TRAVEL_SPEED,
    DEFAULT_Z_HOP,
    KIND,
)
from .messages import park_pair_required
from .types import PauseResumeHints, PauseResumeSettings


def _pair(
    user: dict, x_key: str, y_key: str
) -> tuple[Optional[float], Optional[float]]:
    has_x = present(user, x_key)
    has_y = present(user, y_key)
    if has_x != has_y:
        raise ValueError(park_pair_required(x_key, y_key))
    if not has_x:
        return None, None
    return as_float(user[x_key], x_key), as_float(user[y_key], y_key)


def resolve_pause_settings(user: dict, hints: PauseResumeHints) -> PauseResumeSettings:
    park_x, park_y = _pair(user, "park_x", "park_y")
    cancel_park_x, cancel_park_y = _pair(user, "cancel_park_x", "cancel_park_y")
    max_vel = hints.max_velocity
    travel_speed = pick_speed(
        user, "travel_speed", hints.max_velocity, DEFAULT_TRAVEL_SPEED, max_vel
    )
    if present(user, "z_speed"):
        z_speed = pick_speed(user, "z_speed", None, travel_speed, max_vel)
    else:
        z_speed = travel_speed
    retract = pick_float(user, "retract", hints.retract, DEFAULT_RETRACT)
    retract_speed = pick_float(
        user, "retract_speed", hints.retract_speed, DEFAULT_RETRACT_SPEED
    )
    if present(user, "unretract"):
        unretract = as_float(user["unretract"], "unretract")
    else:
        unretract = retract
    if present(user, "unretract_speed"):
        unretract_speed = as_float(user["unretract_speed"], "unretract_speed")
    else:
        unretract_speed = retract_speed
    return PauseResumeSettings(
        kind=KIND,
        park_x=park_x,
        park_y=park_y,
        z_hop=pick_float(user, "z_hop", hints.z_hop, DEFAULT_Z_HOP),
        travel_speed=travel_speed,
        z_speed=z_speed,
        retract=retract,
        retract_speed=retract_speed,
        unretract=unretract,
        unretract_speed=unretract_speed,
        cancel_retract=pick_float(
            user, "cancel_retract", None, DEFAULT_CANCEL_RETRACT
        ),
        park_at_cancel=pick_bool(user, "park_at_cancel", DEFAULT_PARK_AT_CANCEL),
        cancel_park_x=cancel_park_x,
        cancel_park_y=cancel_park_y,
        idle_timeout=pick_float(user, "idle_timeout", None, DEFAULT_IDLE_TIMEOUT),
        restore_temperature=pick_bool(
            user, "restore_temperature", DEFAULT_RESTORE_TEMPERATURE
        ),
        runout_sensor=pick_optional_str(user, "runout_sensor", None),
    )


def overlay_pause_xy(settings: PauseResumeSettings, x, y) -> PauseResumeSettings:
    """Replace park XY from G-code. Both or neither (caller validates)."""
    return PauseResumeSettings(
        kind=settings.kind,
        park_x=x,
        park_y=y,
        z_hop=settings.z_hop,
        travel_speed=settings.travel_speed,
        z_speed=settings.z_speed,
        retract=settings.retract,
        retract_speed=settings.retract_speed,
        unretract=settings.unretract,
        unretract_speed=settings.unretract_speed,
        cancel_retract=settings.cancel_retract,
        park_at_cancel=settings.park_at_cancel,
        cancel_park_x=settings.cancel_park_x,
        cancel_park_y=settings.cancel_park_y,
        idle_timeout=settings.idle_timeout,
        restore_temperature=settings.restore_temperature,
        runout_sensor=settings.runout_sensor,
    )
