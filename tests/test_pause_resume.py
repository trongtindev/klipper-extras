"""Tests for pause_resume (pure logic + mocked I/O)."""

import re
from pathlib import Path

import pytest

from klipper_extras.constants import CONFIG_OPTION_KEYS
from klipper_extras.features import (
    FEATURE_GCODES,
    FEATURE_KINDS,
    FEATURE_LOADERS,
    feature_gcode_names,
)
from klipper_extras.features.pause_resume import (
    GCODE,
    GCODES,
    KIND,
    OPTION_KEYS,
    REQUIRED_COMPONENTS,
)
from klipper_extras.features.pause_resume.constants import PAUSE_RESUME_HOOK_ACTIONS
from klipper_extras.features.pause_resume.feature import PauseResumeRunner
from klipper_extras.features.pause_resume.resolve import resolve_pause_settings
from klipper_extras.features.pause_resume.types import PauseResumeHints
from klipper_extras.features.pause_resume.validate import validate_pause

HINTS = PauseResumeHints(
    max_velocity=300.0,
    z_hop=None,
    retract=None,
    retract_speed=None,
)


def _resolve(user=None, hints=None):
    return resolve_pause_settings(user or {}, hints if hints is not None else HINTS)


ROOT = Path(__file__).resolve().parents[1]


def test_sample_and_docs_keys_subset():
    keys = OPTION_KEYS
    text = (ROOT / "config" / "sample-pause-resume.cfg").read_text(encoding="utf-8")
    found = set(re.findall(r"^#?\s*([a-z][a-z0-9_]*)\s*:", text, re.M))
    extra = found - keys
    assert not extra, extra
    doc = (ROOT / "docs" / "features" / "pause_resume.md").read_text(encoding="utf-8")
    assert "PAUSE" in doc
    assert "CANCEL_PRINT" in doc
    assert "park_x" in doc
    assert "[respond]" in doc
    assert "[include mainsail.cfg]" in doc


def test_registry():
    assert KIND == "pause_resume"
    assert GCODE == "PAUSE"
    assert GCODES == ("PAUSE", "RESUME", "CANCEL_PRINT")
    assert KIND in FEATURE_LOADERS
    assert FEATURE_GCODES[KIND] == GCODES
    assert feature_gcode_names(KIND) == list(GCODES)
    assert KIND in FEATURE_KINDS
    assert REQUIRED_COMPONENTS == ("virtual_sdcard", "pause_resume", "respond")
    assert "before_pause_gcode" in OPTION_KEYS
    assert "before_resume_gcode" in OPTION_KEYS
    assert "before_cancel_gcode" in OPTION_KEYS
    assert "before_park_gcode" not in OPTION_KEYS
    assert OPTION_KEYS.isdisjoint(CONFIG_OPTION_KEYS)
    assert set(PAUSE_RESUME_HOOK_ACTIONS) == {
        "pause",
        "resume",
        "cancel",
    }


def test_omit_park_xy():
    s = _resolve()
    assert s.park_x is None
    assert s.park_y is None
    assert s.z_hop == 5.0
    assert s.retract == 0.5
    assert s.unretract == 0.5
    assert s.travel_speed == 300.0
    assert s.z_speed == 300.0
    assert s.park_at_cancel is False
    assert s.restore_temperature is True


def test_park_pair_and_hints():
    s = _resolve(
        {"park_x": 10, "park_y": 20},
        PauseResumeHints(max_velocity=150.0, z_hop=8.0, retract=1.2, retract_speed=30.0),
    )
    assert s.park_x == 10.0
    assert s.park_y == 20.0
    assert s.z_hop == 8.0
    assert s.retract == 1.2
    assert s.unretract == 1.2
    assert s.travel_speed == 150.0


def test_one_park_axis_errors():
    with pytest.raises(ValueError, match="park_x"):
        _resolve({"park_x": 10})


def test_travel_speed_capped():
    s = _resolve({"travel_speed": 400})
    assert s.travel_speed == 300.0


def test_unretract_override():
    s = _resolve({"retract": 2, "unretract": 0.5})
    assert s.retract == 2.0
    assert s.unretract == 0.5


def test_validate_negative_z_hop():
    s = _resolve({"z_hop": -1})
    result = validate_pause(s)
    assert result.errors


def test_park_at_cancel_without_xy_warns():
    s = _resolve({"park_at_cancel": True})
    result = validate_pause(s)
    assert not result.errors
    assert result.warnings


class _Gcmd:
    def __init__(self, params=None):
        self._params = params or {}
        self.infos = []

    def get_float(self, name, default=None):
        if name in self._params:
            return float(self._params[name])
        return default

    def respond_info(self, text):
        self.infos.append(text)

    def error(self, text):
        return ValueError(text)


class _Gcode:
    def __init__(self):
        self.scripts = []
        self.commands = {}

    def register_command(self, name, func, desc=None):
        old = self.commands.get(name)
        if func is None:
            self.commands.pop(name, None)
            return old
        self.commands[name] = func
        return None

    def run_script_from_command(self, script):
        self.scripts.append(script)


class _PrintStats:
    def __init__(self, state="printing"):
        self.state = state

    def get_status(self, eventtime):
        return {"state": self.state}


class _Base:
    def __init__(self):
        self.is_paused = False
        self.pause_calls = 0
        self.resume_calls = 0
        self.cancel_calls = 0

    def cmd_PAUSE(self, gcmd):
        self.pause_calls += 1
        self.is_paused = True

    def cmd_RESUME(self, gcmd):
        self.resume_calls += 1
        self.is_paused = False

    def cmd_CANCEL_PRINT(self, gcmd):
        self.cancel_calls += 1
        self.is_paused = False

    def get_status(self, eventtime):
        return {"is_paused": self.is_paused}


class _Heater:
    def __init__(self, can=True, target=200.0):
        self.can_extrude = can
        self._target = target

    def get_temp(self, eventtime):
        return (self._target, self._target)


class _Extruder:
    def __init__(self, heater):
        self._heater = heater

    def get_heater(self):
        return self._heater


class _Coord:
    def __init__(self, z):
        self.z = z


class _Toolhead:
    def __init__(self, homed="xyz", z=0.5, zmax=250.0):
        self._homed = homed
        self._z = z
        self._zmax = zmax

    def get_status(self, eventtime):
        return {"homed_axes": self._homed, "axis_maximum": _Coord(self._zmax)}

    def get_position(self):
        return [0.0, 0.0, self._z, 0.0]


class _Reactor:
    def monotonic(self):
        return 0.0


class _FileConfig:
    def has_option(self, section, option):
        return False


class _Printer:
    def __init__(self, objects):
        self._objects = objects
        self.config_error = ValueError
        self.added = []

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)

    def lookup_objects(self, module=None):
        return list(self._objects.items())

    def add_object(self, name, obj):
        if name in self._objects:
            raise RuntimeError("Printer object '%s' already created" % (name,))
        self._objects[name] = obj
        self.added.append(name)

    def register_event_handler(self, name, callback):
        return None

    def get_reactor(self):
        return _Reactor()


class _Config:
    def __init__(self, printer):
        self._printer = printer
        self.fileconfig = _FileConfig()

    def get_printer(self):
        return self._printer

    def get_name(self):
        return "klipper_extras pause_resume"

    def get(self, key, default=None):
        return default

    def getchoice(self, option, choices, default):
        return default


def _runner(homed="xyz", can_extrude=True, extras=None, print_state="printing"):
    gcode = _Gcode()
    base = _Base()
    objects = {
        "gcode": gcode,
        "klipper_extras": object(),
        "virtual_sdcard": object(),
        "pause_resume": base,
        "respond": object(),
        "print_stats": _PrintStats(print_state),
        "extruder": _Extruder(_Heater(can=can_extrude)),
        "toolhead": _Toolhead(homed=homed),
    }
    if extras:
        objects.update(extras)
    printer = _Printer(objects)
    runner = PauseResumeRunner(_Config(printer))
    runner._handle_connect()
    runner._handle_ready()
    return runner, gcode, base


def test_connect_missing_pause_resume():
    gcode = _Gcode()
    printer = _Printer(
        {
            "gcode": gcode,
            "klipper_extras": object(),
            "virtual_sdcard": object(),
            "respond": object(),
        }
    )
    runner = PauseResumeRunner(_Config(printer))
    with pytest.raises(ValueError, match="pause_resume"):
        runner._handle_connect()


def test_connect_missing_respond():
    gcode = _Gcode()
    printer = _Printer(
        {
            "gcode": gcode,
            "klipper_extras": object(),
            "virtual_sdcard": object(),
            "pause_resume": _Base(),
        }
    )
    runner = PauseResumeRunner(_Config(printer))
    with pytest.raises(ValueError, match="respond"):
        runner._handle_connect()
    assert gcode.commands == {}


def test_connect_does_not_steal_until_ready():
    gcode = _Gcode()
    printer = _Printer(
        {
            "gcode": gcode,
            "klipper_extras": object(),
            "virtual_sdcard": object(),
            "pause_resume": _Base(),
            "respond": object(),
        }
    )
    runner = PauseResumeRunner(_Config(printer))
    runner._handle_connect()
    assert gcode.commands == {}
    assert printer.added == [
        "gcode_macro PAUSE",
        "gcode_macro RESUME",
        "gcode_macro CANCEL_PRINT",
    ]
    runner._handle_ready()
    assert "PAUSE" in gcode.commands
    assert "RESUME" in gcode.commands
    assert "CANCEL_PRINT" in gcode.commands


def test_steal_commands():
    _runner_obj, gcode, _base = _runner()
    assert "PAUSE" in gcode.commands
    assert "RESUME" in gcode.commands
    assert "CANCEL_PRINT" in gcode.commands


def test_pause_retract_and_hop_no_xy():
    runner, gcode, base = _runner()
    runner.cmd_PAUSE(_Gcmd())
    assert base.pause_calls == 1
    joined = "\n".join(gcode.scripts)
    assert "G1 E-" in joined
    assert "G1 Z" in joined
    assert "G1 X" not in joined


def test_pause_with_park():
    runner, gcode, _base = _runner()
    runner.settings = _resolve({"park_x": 10, "park_y": 20, "retract": 0, "z_hop": 0})
    gcode.scripts.clear()
    runner.cmd_PAUSE(_Gcmd())
    joined = "\n".join(gcode.scripts)
    assert "G1 X10.000 Y20.000" in joined


def test_pause_already_paused_skips_base():
    runner, gcode, base = _runner()
    base.is_paused = True
    gcmd = _Gcmd()
    runner.cmd_PAUSE(gcmd)
    assert base.pause_calls == 0
    assert gcmd.infos
    assert gcode.scripts == []


def test_pause_not_printing_skips_base():
    runner, gcode, base = _runner(print_state="standby")
    gcmd = _Gcmd()
    runner.cmd_PAUSE(gcmd)
    assert base.pause_calls == 0
    assert gcmd.infos
    assert gcode.scripts == []


def test_resume_not_paused_skips_base():
    runner, gcode, base = _runner()
    gcmd = _Gcmd()
    runner.cmd_RESUME(gcmd)
    assert base.resume_calls == 0
    assert gcmd.infos
    assert gcode.scripts == []


def test_resume_unretract_then_base():
    runner, gcode, base = _runner()
    runner.cmd_PAUSE(_Gcmd())
    gcode.scripts.clear()
    runner.cmd_RESUME(_Gcmd())
    assert base.resume_calls == 1
    assert any("G1 E" in s and "E-" not in s for s in gcode.scripts)
    assert any("prompt_end" in s for s in gcode.scripts)


def test_resume_cold_prompts_no_base():
    runner, gcode, base = _runner(can_extrude=False)
    runner.settings = _resolve({"restore_temperature": False, "retract": 0, "z_hop": 0})
    base.is_paused = True
    gcode.scripts.clear()
    with pytest.raises(ValueError):
        runner.cmd_RESUME(_Gcmd())
    assert base.resume_calls == 0
    assert any("prompt_begin" in s for s in gcode.scripts)


def test_cancel_heaters_and_base():
    runner, gcode, base = _runner()
    runner.settings = _resolve({"cancel_retract": 0, "z_hop": 0})
    runner.cmd_CANCEL_PRINT(_Gcmd())
    assert base.cancel_calls == 1
    joined = "\n".join(gcode.scripts)
    assert "TURN_OFF_HEATERS" in joined
    assert "M106 S0" in joined


def test_cancel_idle_skips_base():
    runner, gcode, base = _runner(print_state="standby")
    runner.settings = _resolve({"cancel_retract": 0, "z_hop": 0})
    gcmd = _Gcmd()
    runner.cmd_CANCEL_PRINT(gcmd)
    assert base.cancel_calls == 0
    assert gcmd.infos
    assert gcode.scripts == []


def test_cancel_when_paused_runs():
    runner, gcode, base = _runner(print_state="paused")
    runner.settings = _resolve({"cancel_retract": 0, "z_hop": 0})
    base.is_paused = True
    runner.cmd_CANCEL_PRINT(_Gcmd())
    assert base.cancel_calls == 1
    joined = "\n".join(gcode.scripts)
    assert "TURN_OFF_HEATERS" in joined
