"""G-code emission helpers for feature commands (no Klipper imports).

Speeds in this extra are mm/s. G1 ``F`` is mm/min. ``RESTORE_GCODE_STATE``
``MOVE_SPEED`` is already mm/s — do not pass it through ``gcode_feedrate``.
"""

from __future__ import annotations


def gcode_feedrate(speed_mms: float) -> float:
    """G1 ``F`` (mm/min) for a speed in mm/s."""
    return speed_mms * 60.0


def gcode_f(speed_mms: float) -> str:
    return "F%.0f" % (gcode_feedrate(speed_mms),)
