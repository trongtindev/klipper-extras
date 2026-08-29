"""Dataclasses for wipe-motion (pure)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .constants import DEFAULT_Z_HOP


@dataclass(frozen=True)
class WipeKindProfile:
    """Safe defaults for one wipe feature (no machine-specific XY)."""

    wipe_z: float
    travel_z: float
    wipe_speed: float
    travel_speed: float
    passes: int
    pass_offset: float
    retract: float
    retract_speed: float
    fan_speed: float
    z_hop: float = DEFAULT_Z_HOP
    wipe_length: float = 0.0
    start_x: Optional[float] = None
    start_y: Optional[float] = None
    min_nozzle_temp: Optional[float] = None


@dataclass(frozen=True)
class WipeKlipperHints:
    """Values read from Klipper objects at connect. None = not available."""

    max_velocity: Optional[float] = None
    min_nozzle_temp: Optional[float] = None
    retract: Optional[float] = None
    retract_speed: Optional[float] = None
    z_hop: Optional[float] = None
    fan: Optional[str] = None


@dataclass(frozen=True)
class WipePathSettings:
    """Resolved path for one feature instance (never shared across features)."""

    kind: str
    gcode: str
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    wipe_z: float
    z_hop: float
    travel_z: float
    wipe_speed: float
    travel_speed: float
    passes: int
    pass_offset: float
    retract: float
    retract_speed: float
    min_nozzle_temp: Optional[float]
    nozzle_temperature: Optional[float]
    fan_speed: float
    fan: Optional[str]


@dataclass(frozen=True)
class FeatureSpec:
    """Per-feature identity. Options and path live only on this spec/section."""

    kind: str
    gcode: str
    option_keys: frozenset
    help_text: str
    derive_xy: bool
    profile: WipeKindProfile

    def resolve(self, user: dict, hints: Optional[WipeKlipperHints]) -> WipePathSettings:
        from .resolve import resolve_path_settings

        return resolve_path_settings(
            self.kind,
            self.gcode,
            user,
            self.profile,
            hints,
            self.derive_xy,
        )


@dataclass(frozen=True)
class WipeMove:
    """One planned motion. Speeds are mm/s."""

    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    speed: float
    kind: str
