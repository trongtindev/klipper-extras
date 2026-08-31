"""Resolve a wipe path: user → Klipper hint → profile. Pure, no Klipper imports."""

from __future__ import annotations

from typing import Optional

from ...resolve import (
    as_float,
    pick_float,
    pick_int,
    pick_optional_float,
    pick_optional_str,
    pick_speed,
    present,
)
from . import messages as msg
from .constants import MOVE_LIFT, MOVE_TRAVEL, MOVE_WIPE
from .types import (
    WipeActionStep,
    WipeKindProfile,
    WipeKlipperHints,
    WipeMove,
    WipePathSettings,
)


def _resolve_xy(
    kind: str,
    user: dict,
    profile: WipeKindProfile,
    derive_xy: bool,
) -> tuple:
    if derive_xy:
        if profile.start_x is None or profile.start_y is None:
            raise ValueError(msg.xy_required(kind))
        start_x = (
            as_float(user["start_x"], "start_x")
            if present(user, "start_x")
            else float(profile.start_x)
        )
        start_y = (
            as_float(user["start_y"], "start_y")
            if present(user, "start_y")
            else float(profile.start_y)
        )
        length = pick_float(user, "wipe_length", None, profile.wipe_length)
        return (start_x, start_y, start_x + length, start_y)
    have = {k: present(user, k) for k in ("start_x", "start_y", "end_x", "end_y")}
    if not all(have.values()):
        raise ValueError(msg.xy_required(kind))
    return (
        as_float(user["start_x"], "start_x"),
        as_float(user["start_y"], "start_y"),
        as_float(user["end_x"], "end_x"),
        as_float(user["end_y"], "end_y"),
    )


def resolve_path_settings(
    kind: str,
    gcode: str,
    user: dict,
    profile: WipeKindProfile,
    hints: Optional[WipeKlipperHints],
    derive_xy: bool,
) -> WipePathSettings:
    """Build an isolated path snapshot for one feature instance."""
    if hints is None:
        hints = WipeKlipperHints()
    start_x, start_y, end_x, end_y = _resolve_xy(kind, user, profile, derive_xy)
    nozzle_temperature = None
    if present(user, "nozzle_temperature"):
        nozzle_temperature = as_float(user["nozzle_temperature"], "nozzle_temperature")
    fan = pick_optional_str(user, "fan", hints.fan)
    z_hop = pick_float(user, "z_hop", hints.z_hop, profile.z_hop)
    return WipePathSettings(
        kind=kind,
        gcode=gcode,
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        wipe_z=pick_float(user, "wipe_z", None, profile.wipe_z),
        z_hop=z_hop,
        travel_z=pick_float(user, "travel_z", None, profile.travel_z),
        wipe_speed=pick_speed(
            user, "wipe_speed", None, profile.wipe_speed, hints.max_velocity
        ),
        travel_speed=pick_speed(
            user,
            "travel_speed",
            hints.max_velocity,
            profile.travel_speed,
            hints.max_velocity,
        ),
        passes=pick_int(user, "passes", profile.passes),
        pass_offset=pick_float(user, "pass_offset", None, profile.pass_offset),
        retract=pick_float(user, "retract", hints.retract, profile.retract),
        retract_speed=pick_float(
            user, "retract_speed", hints.retract_speed, profile.retract_speed
        ),
        min_nozzle_temp=pick_optional_float(
            user, "min_nozzle_temp", hints.min_nozzle_temp
        ),
        nozzle_temperature=nozzle_temperature,
        fan_speed=pick_float(user, "fan_speed", None, profile.fan_speed),
        fan=fan,
    )


def _pass_perp_positions(
    passes: int, start: float, end: float, pass_offset: float
) -> list[float]:
    """Perpendicular coordinate for each pass.

    Non-zero ``pass_offset``: ``start + i * pass_offset`` (not clamped to end).
    Else space ``passes`` from start to end so a rectangle uses both edges.
    """
    if pass_offset != 0.0:
        return [start + i * pass_offset for i in range(passes)]
    span = end - start
    if passes == 1 or span == 0.0:
        return [start] * passes
    step = span / float(passes - 1)
    return [start + i * step for i in range(passes)]


def plan_wipe_moves(settings: WipePathSettings) -> list[WipeMove]:
    """Lift Z in place, XY at travel_z, drop, N back-forth passes, lift. Speeds mm/s."""
    s = settings
    dx = s.end_x - s.start_x
    dy = s.end_y - s.start_y
    along_x = abs(dx) >= abs(dy)
    moves = [
        WipeMove(None, None, s.z_hop, s.travel_speed, MOVE_TRAVEL),
        WipeMove(s.start_x, s.start_y, s.travel_z, s.travel_speed, MOVE_TRAVEL),
        WipeMove(s.start_x, s.start_y, s.wipe_z, s.travel_speed, MOVE_TRAVEL),
    ]
    if along_x:
        perps = _pass_perp_positions(s.passes, s.start_y, s.end_y, s.pass_offset)
        for i, y in enumerate(perps):
            x_start, x_end = (
                (s.start_x, s.end_x) if i % 2 == 0 else (s.end_x, s.start_x)
            )
            moves.append(WipeMove(x_start, y, s.wipe_z, s.wipe_speed, MOVE_WIPE))
            moves.append(WipeMove(x_end, y, s.wipe_z, s.wipe_speed, MOVE_WIPE))
    else:
        perps = _pass_perp_positions(s.passes, s.start_x, s.end_x, s.pass_offset)
        for i, x in enumerate(perps):
            y_start, y_end = (
                (s.start_y, s.end_y) if i % 2 == 0 else (s.end_y, s.start_y)
            )
            moves.append(WipeMove(x, y_start, s.wipe_z, s.wipe_speed, MOVE_WIPE))
            moves.append(WipeMove(x, y_end, s.wipe_z, s.wipe_speed, MOVE_WIPE))
    last = moves[-1]
    moves.append(WipeMove(last.x, last.y, s.travel_z, s.travel_speed, MOVE_LIFT))
    return moves


def plan_wipe_actions(settings: WipePathSettings) -> list:
    """Group planned moves into named actions (z_hop, travel, lower, pass, lift)."""
    moves = plan_wipe_moves(settings)
    steps = [
        WipeActionStep("z_hop", (moves[0],)),
        WipeActionStep("travel", (moves[1],)),
        WipeActionStep("lower", (moves[2],)),
    ]
    mid = moves[3:-1]
    pass_index = 0
    for i in range(0, len(mid), 2):
        steps.append(WipeActionStep("pass", tuple(mid[i : i + 2]), pass_index=pass_index))
        pass_index += 1
    steps.append(WipeActionStep("lift", (moves[-1],)))
    return steps
