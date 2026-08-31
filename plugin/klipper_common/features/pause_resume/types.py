"""Dataclasses for pause_resume (pure)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PauseResumeHints:
    """Live Klipper fields at connect. None = not available."""

    max_velocity: Optional[float] = None
    z_hop: Optional[float] = None
    retract: Optional[float] = None
    retract_speed: Optional[float] = None


@dataclass(frozen=True)
class PauseResumeSettings:
    """Resolved settings for one pause_resume instance."""

    kind: str
    park_x: Optional[float]
    park_y: Optional[float]
    z_hop: float
    travel_speed: float
    z_speed: float
    retract: float
    retract_speed: float
    unretract: float
    unretract_speed: float
    cancel_retract: float
    park_at_cancel: bool
    cancel_park_x: Optional[float]
    cancel_park_y: Optional[float]
    idle_timeout: float
    restore_temperature: bool
    runout_sensor: Optional[str]
