"""SAVE / RESTORE_GCODE_STATE for feature commands.

NAME is the feature G-code (``PAUSE``, ``FORM_TIP``, …). ``MOVE`` is a
command param (``0`` or ``1``; default ``0`` keeps XYZ). Not a section option.
"""

from __future__ import annotations


def parse_restore_move(gcmd) -> int:
    return gcmd.get_int("MOVE", 0, minval=0, maxval=1)
