"""Dataclasses for form_tip (pure)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FormTipProfile:
    """Safe defaults for one tip-forming profile. Machine-agnostic numbers.
    All-zero/None means no default — user must set or use a named profile."""

    unloading_speed_start_len: float = 0.0
    unloading_speed_start: float = 0.0
    ramming_len: float = 0.0
    ramming_speed: float = 0.0
    tip_distance: float = 0.0
    sep_fast_len: float = 0.0
    sep_fast_speed: float = 0.0
    sep_slow_speed: float = 0.0
    cooling_moves: int = 0
    cool_len: float = 0.0
    cool_speed_slow: float = 0.0
    cool_speed_fast: float = 0.0
    use_skinnydip: bool = False
    dip_in: float = 0.0
    dip_in_speed: float = 0.0
    dip_out_speed: float = 0.0
    pause_melt_ms: int = 0
    pause_cool_ms: int = 0
    parking_distance: float = 0.0
    park_speed: float = 0.0
    fan_speed: float = 0.0
    fan: Optional[str] = None
    min_nozzle_temp: Optional[float] = None
    nozzle_temperature: Optional[float] = None


@dataclass(frozen=True)
class FormTipHints:
    """Values read from Klipper objects at connect. None = not available."""

    max_extrude_only_velocity: Optional[float] = None
    min_nozzle_temp: Optional[float] = None
    fan: Optional[str] = None


@dataclass(frozen=True)
class FormTipSettings:
    """Resolved settings for one form_tip instance (never shared across features)."""

    kind: str
    gcode: str
    profile_name: Optional[str]
    tip_distance: float
    unloading_speed_start_len: float
    unloading_speed_start: float
    ramming_len: float
    ramming_speed: float
    sep_fast_len: float
    sep_fast_speed: float
    sep_slow_speed: float
    cooling_moves: int
    cool_len: float
    cool_speed_slow: float
    cool_speed_fast: float
    use_skinnydip: bool
    dip_in: float
    dip_in_speed: float
    dip_out_speed: float
    pause_melt_ms: int
    pause_cool_ms: int
    parking_distance: float
    park_speed: float
    fan_speed: float
    fan: Optional[str]
    min_nozzle_temp: Optional[float]
    nozzle_temperature: Optional[float]

    @property
    def sep_slow_len(self) -> float:
        """Computed separation slow length = tip_distance - unload_start - sep_fast."""
        return self.tip_distance - self.unloading_speed_start_len - self.sep_fast_len


@dataclass(frozen=True)
class FormTipStep:
    """One planned tip-forming step. command is raw G-code to emit."""

    command: str
    label: str  # for logging / debugging
