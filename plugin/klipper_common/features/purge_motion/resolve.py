"""Resolve a purge path: user → Klipper hint → profile. Pure, no Klipper imports."""

from __future__ import annotations

import math
from dataclasses import replace as dataclass_replace
from typing import Optional

from ...resolve import (
    as_float,
    clamp_speed,
    pick_float,
    pick_optional_str,
    pick_speed,
    present,
)
from . import messages as msg
from .constants import (
    ALONG_CHOICES,
    ALONG_X,
    ALONG_Y,
    BED_STYLES,
    BREAK_TRAVEL,
    MOVE_LIFT,
    MOVE_PURGE,
    MOVE_TRAVEL,
    ORIGIN_ADAPTIVE,
    ORIGIN_FIXED,
    STYLE_LINE,
    STYLE_VORON,
)
from .styles import strokes_for_style
from .types import (
    PurgeActionStep,
    PurgeKindProfile,
    PurgeKlipperHints,
    PurgeMove,
    PurgePathSettings,
)


def heat_wait_target(
    nozzle_temperature: Optional[float],
    min_nozzle_temp: Optional[float],
    current: float,
    heater_target: float,
) -> Optional[float]:
    """M109 target °C, or None if already at the floor. Caller supplies a floor."""
    if nozzle_temperature is not None:
        return float(nozzle_temperature)
    minimum = float(min_nozzle_temp)
    if current >= minimum:
        return None
    if heater_target >= minimum:
        return float(heater_target)
    return minimum


def _pick_min_nozzle_temp(user: dict, hints: PurgeKlipperHints) -> Optional[float]:
    """Purge section > [klipper_common] > [extruder] min_extrude_temp."""
    if present(user, "min_nozzle_temp"):
        return as_float(user["min_nozzle_temp"], "min_nozzle_temp")
    if hints.host_min_nozzle_temp is not None:
        return float(hints.host_min_nozzle_temp)
    if hints.min_nozzle_temp is not None:
        return float(hints.min_nozzle_temp)
    return None


def filament_area(diameter: float) -> float:
    return math.pi * (diameter / 2.0) ** 2


def e_speed_mms(flow_rate: float, diameter: float) -> float:
    area = filament_area(diameter)
    if area <= 0:
        raise ValueError(msg.filament_diameter_invalid())
    return flow_rate / area


def _resolve_style(user: dict, profile: PurgeKindProfile, move_while_purge: bool):
    if not move_while_purge:
        if present(user, "style"):
            raise ValueError(msg.style_key_conflict("style", "pose"))
        return None, None, None
    if present(user, "style"):
        style = str(user["style"]).strip().lower()
    else:
        style = str(profile.style)
    if style not in BED_STYLES:
        raise ValueError(msg.unknown_style(style, ", ".join(sorted(BED_STYLES))))
    along = None
    style_size = None
    if style == STYLE_LINE:
        if present(user, "style_size"):
            raise ValueError(msg.style_key_conflict("style_size", style))
        if present(user, "along"):
            along = str(user["along"]).strip().lower()
        else:
            along = str(profile.along)
        if along not in ALONG_CHOICES:
            raise ValueError(msg.unknown_along(along))
    else:
        if present(user, "along"):
            raise ValueError(msg.style_key_conflict("along", style))
        if present(user, "purge_length"):
            raise ValueError(msg.style_key_conflict("purge_length", style))
        style_size = pick_float(user, "style_size", None, profile.style_size)
    return style, along, style_size


def _resolve_origin(kind: str, user: dict, require_pose: bool):
    have_x = present(user, "start_x")
    have_y = present(user, "start_y")
    if require_pose:
        if not (have_x and have_y):
            raise ValueError(msg.pose_required(kind))
        return (
            ORIGIN_FIXED,
            as_float(user["start_x"], "start_x"),
            as_float(user["start_y"], "start_y"),
        )
    if have_x != have_y:
        raise ValueError(msg.xy_partial())
    if have_x and have_y:
        return (
            ORIGIN_FIXED,
            as_float(user["start_x"], "start_x"),
            as_float(user["start_y"], "start_y"),
        )
    return ORIGIN_ADAPTIVE, None, None


def resolve_path_settings(
    kind: str,
    gcode: str,
    user: dict,
    profile: PurgeKindProfile,
    hints: Optional[PurgeKlipperHints],
    move_while_purge: bool,
    require_pose: bool,
) -> PurgePathSettings:
    """Build an isolated snapshot for one feature instance."""
    if hints is None:
        hints = PurgeKlipperHints()
    if hints.filament_diameter is None:
        raise ValueError(msg.filament_diameter_required())
    diameter = float(hints.filament_diameter)
    if diameter <= 0:
        raise ValueError(msg.filament_diameter_invalid())
    origin_mode, start_x, start_y = _resolve_origin(kind, user, require_pose)
    style, along, style_size = _resolve_style(user, profile, move_while_purge)
    if require_pose:
        if not present(user, "purge_z"):
            raise ValueError(msg.purge_z_required(kind))
        purge_z = as_float(user["purge_z"], "purge_z")
    else:
        purge_z = pick_float(user, "purge_z", None, float(profile.purge_z))
    nozzle_temperature = None
    if present(user, "nozzle_temperature"):
        nozzle_temperature = as_float(user["nozzle_temperature"], "nozzle_temperature")
    fan = pick_optional_str(user, "fan", hints.fan)
    z_hop = pick_float(user, "z_hop", hints.z_hop, profile.z_hop)
    purge_amount = pick_float(user, "purge_amount", None, profile.purge_amount)
    purge_length = None
    purge_margin = None
    if move_while_purge:
        purge_margin = pick_float(user, "purge_margin", None, profile.purge_margin)
        if style == STYLE_LINE:
            purge_length = pick_float(user, "purge_length", None, purge_amount)
    min_nozzle_temp = _pick_min_nozzle_temp(user, hints)
    if min_nozzle_temp is None and nozzle_temperature is None:
        raise ValueError(msg.heat_temp_required(kind))
    return PurgePathSettings(
        kind=kind,
        gcode=gcode,
        move_while_purge=move_while_purge,
        origin_mode=origin_mode,
        start_x=start_x,
        start_y=start_y,
        purge_z=purge_z,
        z_hop=z_hop,
        travel_z=pick_float(user, "travel_z", None, profile.travel_z),
        travel_speed=pick_speed(
            user,
            "travel_speed",
            hints.max_velocity,
            profile.travel_speed,
            hints.max_velocity,
        ),
        purge_amount=purge_amount,
        flow_rate=pick_float(user, "flow_rate", None, profile.flow_rate),
        tip_distance=pick_float(user, "tip_distance", None, profile.tip_distance),
        retract=pick_float(user, "retract", hints.retract, profile.retract),
        retract_speed=pick_float(
            user, "retract_speed", hints.retract_speed, profile.retract_speed
        ),
        filament_diameter=diameter,
        min_nozzle_temp=min_nozzle_temp,
        nozzle_temperature=nozzle_temperature,
        fan_speed=pick_float(user, "fan_speed", None, profile.fan_speed),
        fan=fan,
        style=style,
        along=along,
        style_size=style_size,
        purge_length=purge_length,
        purge_margin=purge_margin,
        max_velocity=hints.max_velocity,
        max_extrude_cross_section=hints.max_extrude_cross_section,
        max_extrude_only_velocity=hints.max_extrude_only_velocity,
        axis_minimum_x=hints.axis_minimum_x,
        axis_minimum_y=hints.axis_minimum_y,
        axis_maximum_x=hints.axis_maximum_x,
        axis_maximum_y=hints.axis_maximum_y,
    )


def overlay_purge_amount(
    settings: PurgePathSettings, amount: Optional[float]
) -> PurgePathSettings:
    """Return a copy with purge_amount replaced. Does not mutate ``settings``."""
    if amount is None:
        return settings
    value = as_float(amount, "purge_amount")
    return dataclass_replace(settings, purge_amount=value)


def resolve_bed_origin(settings: PurgePathSettings, aabb) -> tuple:
    """Return (ox, oy). ``aabb`` is (x_min, y_min, x_max, y_max) or None."""
    if settings.origin_mode == ORIGIN_FIXED:
        if settings.start_x is None or settings.start_y is None:
            raise ValueError(msg.origin_not_resolved())
        return float(settings.start_x), float(settings.start_y)
    if aabb is None:
        raise ValueError(msg.adaptive_needs_objects())
    x_min, y_min, x_max, y_max = aabb
    margin = float(settings.purge_margin or 0.0)
    if settings.style == STYLE_VORON:
        return x_min - margin, y_min - margin
    length = float(settings.purge_length or 0.0)
    if settings.along == ALONG_Y:
        mid = (y_min + y_max) / 2.0
        return x_min - margin, mid - length / 2.0
    mid = (x_min + x_max) / 2.0
    return mid - length / 2.0, y_min - margin


def _check_xy(settings: PurgePathSettings, x: float, y: float) -> None:
    if settings.axis_minimum_x is not None and x < settings.axis_minimum_x:
        raise ValueError(msg.out_of_range("x", x, settings.axis_minimum_x))
    if settings.axis_maximum_x is not None and x > settings.axis_maximum_x:
        raise ValueError(msg.out_of_range("x", x, settings.axis_maximum_x))
    if settings.axis_minimum_y is not None and y < settings.axis_minimum_y:
        raise ValueError(msg.out_of_range("y", y, settings.axis_minimum_y))
    if settings.axis_maximum_y is not None and y > settings.axis_maximum_y:
        raise ValueError(msg.out_of_range("y", y, settings.axis_maximum_y))


def _xy_speed(e_speed: float, seg_len: float, e_seg: float, max_velocity: Optional[float]) -> float:
    if e_seg <= 0 or seg_len <= 0:
        raise ValueError(msg.length_not_positive())
    speed = e_speed * seg_len / e_seg
    return clamp_speed(speed, max_velocity)


def _bead_cross_section(area: float, e_seg: float, seg_len: float) -> float:
    if seg_len <= 0:
        raise ValueError(msg.length_not_positive())
    return area * e_seg / seg_len


def _check_cross_section(settings: PurgePathSettings, needed: float) -> None:
    current = settings.max_extrude_cross_section
    if current is None:
        return
    if needed > current:
        raise ValueError(msg.cross_section_too_small(current, needed))


def _e_move(delta: float, speed: float) -> PurgeMove:
    return PurgeMove(None, None, None, delta, speed, MOVE_PURGE)


def _xyz(x, y, z, speed, kind, e=None) -> PurgeMove:
    return PurgeMove(x, y, z, e, speed, kind)


def plan_purge_actions(settings: PurgePathSettings) -> list:
    """Named actions after origin is resolved. Speeds mm/s."""
    s = settings
    if s.start_x is None or s.start_y is None:
        raise ValueError(msg.origin_not_resolved())
    ox, oy = float(s.start_x), float(s.start_y)
    e_speed = e_speed_mms(s.flow_rate, s.filament_diameter)
    if s.max_extrude_only_velocity is not None and s.max_extrude_only_velocity > 0:
        e_speed = min(e_speed, s.max_extrude_only_velocity)
    if e_speed <= 0:
        raise ValueError(msg.speed_not_positive("flow_rate"))
    area = filament_area(s.filament_diameter)
    steps = [
        PurgeActionStep(
            "z_hop",
            (_xyz(None, None, s.z_hop, s.travel_speed, MOVE_TRAVEL),),
        ),
    ]
    if not s.move_while_purge:
        _check_xy(s, ox, oy)
        steps.append(
            PurgeActionStep(
                "travel",
                (_xyz(ox, oy, s.travel_z, s.travel_speed, MOVE_TRAVEL),),
            )
        )
        steps.append(
            PurgeActionStep(
                "lower",
                (_xyz(ox, oy, s.purge_z, s.travel_speed, MOVE_TRAVEL),),
            )
        )
        if s.tip_distance > 0:
            steps.append(
                PurgeActionStep("tip", (_e_move(s.tip_distance, e_speed),))
            )
        steps.append(
            PurgeActionStep(
                "purge",
                (_e_move(s.purge_amount, e_speed),),
                pass_index=0,
            )
        )
        if s.retract > 0:
            steps.append(
                PurgeActionStep(
                    "retract",
                    (_e_move(-s.retract, s.retract_speed),),
                )
            )
        steps.append(
            PurgeActionStep(
                "lift",
                (_xyz(ox, oy, s.travel_z, s.travel_speed, MOVE_LIFT),),
            )
        )
        return steps

    style = s.style or STYLE_LINE
    along = s.along or ALONG_X
    length = float(s.purge_length or 0.0)
    size = float(s.style_size or 0.0)
    strokes = strokes_for_style(style, ox, oy, length, along, size)
    if not strokes:
        raise ValueError(msg.unknown_style(style, ", ".join(sorted(BED_STYLES))))
    first = strokes[0]
    _check_xy(s, first.start_x, first.start_y)
    steps.append(
        PurgeActionStep(
            "travel",
            (_xyz(first.start_x, first.start_y, s.travel_z, s.travel_speed, MOVE_TRAVEL),),
        )
    )
    steps.append(
        PurgeActionStep(
            "lower",
            (_xyz(first.start_x, first.start_y, s.purge_z, s.travel_speed, MOVE_TRAVEL),),
        )
    )
    if s.tip_distance > 0:
        steps.append(PurgeActionStep("tip", (_e_move(s.tip_distance, e_speed),)))
    last_x, last_y = first.start_x, first.start_y
    for i, stroke in enumerate(strokes):
        _check_xy(s, stroke.start_x, stroke.start_y)
        _check_xy(s, stroke.end_x, stroke.end_y)
        if i > 0:
            if s.retract > 0:
                steps.append(
                    PurgeActionStep(
                        "retract",
                        (_e_move(-s.retract, s.retract_speed),),
                    )
                )
            steps.append(
                PurgeActionStep(
                    "lift",
                    (_xyz(last_x, last_y, s.travel_z, s.travel_speed, MOVE_LIFT),),
                )
            )
            steps.append(
                PurgeActionStep(
                    "travel",
                    (
                        _xyz(
                            stroke.start_x,
                            stroke.start_y,
                            s.travel_z,
                            s.travel_speed,
                            MOVE_TRAVEL,
                        ),
                    ),
                )
            )
            steps.append(
                PurgeActionStep(
                    "lower",
                    (
                        _xyz(
                            stroke.start_x,
                            stroke.start_y,
                            s.purge_z,
                            s.travel_speed,
                            MOVE_TRAVEL,
                        ),
                    ),
                )
            )
            if s.retract > 0:
                steps.append(
                    PurgeActionStep(
                        "recover",
                        (_e_move(s.retract, s.retract_speed),),
                    )
                )
        seg_len = math.hypot(stroke.end_x - stroke.start_x, stroke.end_y - stroke.start_y)
        e_seg = s.purge_amount * stroke.e_fraction
        xy_speed = _xy_speed(e_speed, seg_len, e_seg, s.max_velocity)
        _check_cross_section(s, _bead_cross_section(area, e_seg, seg_len))
        steps.append(
            PurgeActionStep(
                "purge",
                (
                    _xyz(
                        stroke.end_x,
                        stroke.end_y,
                        s.purge_z,
                        xy_speed,
                        MOVE_PURGE,
                        e=e_seg,
                    ),
                ),
                pass_index=i,
            )
        )
        last_x, last_y = stroke.end_x, stroke.end_y
    if s.retract > 0:
        steps.append(
            PurgeActionStep(
                "retract",
                (_e_move(-s.retract, s.retract_speed),),
            )
        )
    if style == STYLE_LINE:
        last = strokes[0]
        if along == ALONG_Y:
            bx, by = last.end_x, last.end_y + BREAK_TRAVEL
        else:
            bx, by = last.end_x + BREAK_TRAVEL, last.end_y
        _check_xy(s, bx, by)
        steps.append(
            PurgeActionStep(
                "break",
                (_xyz(bx, by, s.purge_z, s.travel_speed, MOVE_TRAVEL),),
            )
        )
        last_x, last_y = bx, by
    steps.append(
        PurgeActionStep(
            "lift",
            (_xyz(last_x, last_y, s.travel_z, s.travel_speed, MOVE_LIFT),),
        )
    )
    return steps
