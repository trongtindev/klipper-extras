"""Shared G-code helpers (feedrate + SAVE/RESTORE MOVE)."""

import pytest

from klipper_extras.features.gcode import gcode_f, gcode_feedrate
from klipper_extras.features.gcode_state import parse_restore_move


class _FakeGcmd:
    def __init__(self, params=None):
        self._params = params or {}

    def get_int(self, name, default=None, minval=None, maxval=None):
        val = self._params.get(name, default)
        if val is None:
            return default
        iv = int(val)
        if minval is not None and iv < minval:
            raise RuntimeError("%s must be >= %s" % (name, minval))
        if maxval is not None and iv > maxval:
            raise RuntimeError("%s must be <= %s" % (name, maxval))
        return iv


def test_gcode_feedrate_mms_to_mm_min():
    assert gcode_feedrate(1.0) == 60.0
    assert gcode_feedrate(200.0) == 12000.0
    assert gcode_f(200.0) == "F12000"


def test_parse_restore_move_default_zero():
    assert parse_restore_move(_FakeGcmd()) == 0


def test_parse_restore_move_one():
    assert parse_restore_move(_FakeGcmd({"MOVE": 1})) == 1


def test_parse_restore_move_rejects_out_of_range():
    with pytest.raises(RuntimeError, match="MOVE must be <= 1"):
        parse_restore_move(_FakeGcmd({"MOVE": 2}))
    with pytest.raises(RuntimeError, match="MOVE must be >= 0"):
        parse_restore_move(_FakeGcmd({"MOVE": -1}))
