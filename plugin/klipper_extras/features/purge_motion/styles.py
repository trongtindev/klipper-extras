"""Bed purge styles (line + voron). Pure; offsets are relative, not machine pose."""

from __future__ import annotations

from .constants import ALONG_Y, STYLE_LINE, STYLE_VORON
from .types import PurgeStroke

# Voron-style fractions of style_size (origin = bottom-left).
VORON_STROKES = (
    ((0.0, 0.5), (0.289, 1.0), 0.25),
    ((0.789, 1.0), (0.211, 0.0), 0.5),
    ((0.711, 0.0), (1.0, 0.5), 0.25),
)


def line_strokes(origin_x: float, origin_y: float, length: float, along: str) -> tuple:
    """One stroke from origin along X or Y."""
    if along == ALONG_Y:
        end_x, end_y = origin_x, origin_y + length
    else:
        end_x, end_y = origin_x + length, origin_y
    return (
        PurgeStroke(origin_x, origin_y, end_x, end_y, 1.0),
    )


def voron_strokes(origin_x: float, origin_y: float, size: float) -> tuple:
    """Three logo strokes relative to origin."""
    strokes = []
    for (sx, sy), (ex, ey), frac in VORON_STROKES:
        strokes.append(
            PurgeStroke(
                origin_x + sx * size,
                origin_y + sy * size,
                origin_x + ex * size,
                origin_y + ey * size,
                frac,
            )
        )
    return tuple(strokes)


def strokes_for_style(
    style: str,
    origin_x: float,
    origin_y: float,
    purge_length: float,
    along: str,
    style_size: float,
) -> tuple:
    if style == STYLE_VORON:
        return voron_strokes(origin_x, origin_y, style_size)
    if style == STYLE_LINE:
        return line_strokes(origin_x, origin_y, purge_length, along)
    return ()
