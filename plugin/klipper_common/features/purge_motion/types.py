"""Dataclasses for purge-motion (pure)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .constants import DEFAULT_Z_HOP, STYLE_LINE


@dataclass(frozen=True)
class PurgeKindProfile:
    """Safe defaults for one purge feature (no machine-specific XY)."""

    purge_amount: float
    flow_rate: float
    travel_z: float
    travel_speed: float
    retract: float
    retract_speed: float
    fan_speed: float
    tip_distance: float = 0.0
    purge_z: Optional[float] = None
    z_hop: float = DEFAULT_Z_HOP
    style: str = STYLE_LINE
    along: str = "x"
    style_size: float = 10.0
    purge_margin: float = 10.0
    min_nozzle_temp: Optional[float] = None


@dataclass(frozen=True)
class PurgeKlipperHints:
    """Values read from Klipper objects at connect. None = not available."""

    max_velocity: Optional[float] = None
    min_nozzle_temp: Optional[float] = None
    host_min_nozzle_temp: Optional[float] = None
    retract: Optional[float] = None
    retract_speed: Optional[float] = None
    z_hop: Optional[float] = None
    fan: Optional[str] = None
    filament_diameter: Optional[float] = None
    max_extrude_cross_section: Optional[float] = None
    max_extrude_only_velocity: Optional[float] = None
    axis_minimum_x: Optional[float] = None
    axis_minimum_y: Optional[float] = None
    axis_maximum_x: Optional[float] = None
    axis_maximum_y: Optional[float] = None


@dataclass(frozen=True)
class PurgePathSettings:
    """Resolved snapshot for one feature instance (never shared across features)."""

    kind: str
    gcode: str
    move_while_purge: bool
    origin_mode: str
    start_x: Optional[float]
    start_y: Optional[float]
    purge_z: float
    z_hop: float
    travel_z: float
    travel_speed: float
    purge_amount: float
    flow_rate: float
    tip_distance: float
    retract: float
    retract_speed: float
    filament_diameter: float
    min_nozzle_temp: Optional[float]
    nozzle_temperature: Optional[float]
    fan_speed: float
    fan: Optional[str]
    style: Optional[str] = None
    along: Optional[str] = None
    style_size: Optional[float] = None
    purge_length: Optional[float] = None
    purge_margin: Optional[float] = None
    max_velocity: Optional[float] = None
    max_extrude_cross_section: Optional[float] = None
    max_extrude_only_velocity: Optional[float] = None
    axis_minimum_x: Optional[float] = None
    axis_minimum_y: Optional[float] = None
    axis_maximum_x: Optional[float] = None
    axis_maximum_y: Optional[float] = None


@dataclass(frozen=True)
class FeatureSpec:
    """Per-feature identity. Options and path live only on this spec/section."""

    kind: str
    gcode: str
    option_keys: frozenset
    help_text: str
    move_while_purge: bool
    require_pose: bool
    profile: PurgeKindProfile

    def resolve(self, user: dict, hints: Optional[PurgeKlipperHints]) -> PurgePathSettings:
        from .resolve import resolve_path_settings

        return resolve_path_settings(
            self.kind,
            self.gcode,
            user,
            self.profile,
            hints,
            self.move_while_purge,
            self.require_pose,
        )


@dataclass(frozen=True)
class PurgeMove:
    """One planned motion. Speeds are mm/s. ``e`` is relative extrusion mm."""

    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    e: Optional[float]
    speed: float
    kind: str


@dataclass(frozen=True)
class PurgeActionStep:
    """One named purge action with its moves (for per-action hooks)."""

    name: str
    moves: tuple
    pass_index: Optional[int] = None


@dataclass(frozen=True)
class PurgeStroke:
    """One XY stroke in style space (mm), with filament fraction of purge_amount."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    e_fraction: float
