import logging

import pytest

from klipper_common.constants import MIN_EXTRUDE_TEMP_HEAT_MARGIN
from klipper_common.features.wipe_motion.constants import (
    CMD_ABSOLUTE,
    CMD_RESTORE_GCODE_STATE,
    CMD_SAVE_GCODE_STATE,
    DEFAULT_TRAVEL_Z,
    MOVE_LIFT,
    MOVE_TRAVEL,
    MOVE_WIPE,
)
from klipper_common.features.wipe_motion.hints import collect_wipe_hints
from klipper_common.features.wipe_motion.messages import skip_nozzle_wait
from klipper_common.features.wipe_motion.resolve import plan_wipe_actions, plan_wipe_moves
from klipper_common.features.wipe_motion.runner import WipeRunner
from klipper_common.features.wipe_motion.types import WipeKlipperHints
from klipper_common.features.wipe_motion.validate import validate_path
from klipper_common.features.wipe_nozzle_on_bed.constants import (
    DEFAULT_PASS_OFFSET as BED_PASS_OFFSET,
    DEFAULT_PASSES as BED_PASSES,
    DEFAULT_START_X as BED_START_X,
    DEFAULT_START_Y as BED_START_Y,
    DEFAULT_STRIP_LENGTH as BED_STRIP_LENGTH,
    DEFAULT_WIPE_SPEED as BED_WIPE_SPEED,
    DEFAULT_WIPE_Z as BED_WIPE_Z,
    GCODE as BED_GCODE,
    KIND as BED_KIND,
    SPEC as BED_SPEC,
)
from klipper_common.features.wipe_nozzle_on_rubber.constants import (
    DEFAULT_PASSES as RUBBER_PASSES,
    DEFAULT_WIPE_SPEED as RUBBER_WIPE_SPEED,
    DEFAULT_WIPE_Z as RUBBER_WIPE_Z,
    GCODE as RUBBER_GCODE,
    KIND as RUBBER_KIND,
    SPEC as RUBBER_SPEC,
)

HINTS = WipeKlipperHints(max_velocity=300.0)

RUBBER_XY = {
    "start_x": 10,
    "start_y": 20,
    "end_x": 50,
    "end_y": 20,
}


def _bed(user=None, hints=None):
    return BED_SPEC.resolve(user or {}, hints if hints is not None else HINTS)


def _rubber(user=None, hints=None):
    data = dict(RUBBER_XY)
    if user:
        data.update(user)
    return RUBBER_SPEC.resolve(data, hints if hints is not None else HINTS)


def test_gcode_and_kind_owned():
    assert BED_SPEC.kind == BED_KIND
    assert RUBBER_SPEC.kind == RUBBER_KIND
    assert BED_SPEC.gcode == BED_GCODE
    assert RUBBER_SPEC.gcode == RUBBER_GCODE
    assert BED_SPEC.gcode != RUBBER_SPEC.gcode


def test_user_beats_hint_beats_profile():
    hints = WipeKlipperHints(
        min_nozzle_temp=180.0,
        retract=1.2,
        max_velocity=300.0,
    )
    s = _bed({"min_nozzle_temp": 200, "retract": 0.3, "wipe_z": 0.4}, hints)
    assert s.min_nozzle_temp == 200.0
    assert s.retract == 0.3
    assert s.wipe_z == 0.4
    s2 = _bed({}, hints)
    assert s2.min_nozzle_temp == 180.0
    assert s2.retract == 1.2
    assert s2.wipe_z == BED_WIPE_Z
    s3 = _bed({}, WipeKlipperHints())
    assert s3.min_nozzle_temp is None
    text = skip_nozzle_wait()
    assert "skipping nozzle wait" in text
    assert "retract" not in text


def test_bed_empty_is_horizontal_safe_strip():
    s = _bed({}, WipeKlipperHints())
    assert s.start_x == BED_START_X
    assert s.start_y == BED_START_Y
    assert s.end_x == BED_START_X + BED_STRIP_LENGTH
    assert s.end_y == BED_START_Y
    assert s.wipe_speed == BED_WIPE_SPEED
    assert s.wipe_z == BED_WIPE_Z
    assert s.wipe_z == 0.1
    assert s.travel_z == DEFAULT_TRAVEL_Z
    assert s.passes == BED_PASSES
    assert s.passes == 1
    assert s.pass_offset == BED_PASS_OFFSET
    wipes = [m for m in plan_wipe_moves(s) if m.kind == MOVE_WIPE]
    assert len(wipes) == 2
    assert all(m.y == BED_START_Y for m in wipes)


def test_bed_wipe_length_sets_end_x():
    s = _bed({"wipe_length": 20})
    assert s.start_x == BED_START_X
    assert s.end_x == BED_START_X + 20
    assert s.end_y == s.start_y


def test_bed_partial_user_xy_overlays_safe_strip():
    s = _bed({"start_y": 12})
    assert s.start_y == 12.0
    assert s.start_x == BED_START_X
    assert s.end_y == 12.0


def test_travel_z_not_from_z_hop():
    hints = WipeKlipperHints(z_hop=8.0, max_velocity=300.0)
    s = _bed({}, hints)
    assert s.z_hop == 8.0
    assert s.travel_z == DEFAULT_TRAVEL_Z

    s_user = _bed({"z_hop": 3.0, "travel_z": 10.0}, hints)
    assert s_user.z_hop == 3.0
    assert s_user.travel_z == 10.0

    s_no_hint = _bed({}, WipeKlipperHints())
    assert s_no_hint.z_hop == DEFAULT_TRAVEL_Z
    assert s_no_hint.travel_z == DEFAULT_TRAVEL_Z


def test_rubber_empty_user_errors():
    with pytest.raises(ValueError, match="start_x"):
        RUBBER_SPEC.resolve({}, HINTS)


def test_rubber_user_xy_ok():
    s = _rubber()
    assert (s.start_x, s.start_y, s.end_x, s.end_y) == (10.0, 20.0, 50.0, 20.0)
    assert s.wipe_z == RUBBER_WIPE_Z
    assert s.wipe_speed == RUBBER_WIPE_SPEED


def test_bed_ignores_end_xy():
    s = _bed({"end_x": 999, "end_y": 888, "wipe_length": 20})
    assert s.end_x == BED_START_X + 20
    assert s.end_y == BED_START_Y


def test_bed_and_rubber_positions_do_not_collide():
    bed = _bed({"start_x": 5, "start_y": 5, "wipe_length": 40})
    rubber = _rubber(
        {"start_x": 120, "start_y": 180, "end_x": 160, "end_y": 180}
    )
    assert (bed.start_x, bed.start_y, bed.end_x, bed.end_y) == (5.0, 5.0, 45.0, 5.0)
    assert (rubber.start_x, rubber.start_y, rubber.end_x, rubber.end_y) == (
        120.0,
        180.0,
        160.0,
        180.0,
    )
    assert bed.kind != rubber.kind
    assert bed.gcode != rubber.gcode


def test_speed_clamp_to_max_velocity():
    slow = WipeKlipperHints(max_velocity=40.0)
    s = _bed({}, slow)
    assert s.travel_speed == 40.0
    assert s.wipe_speed == 40.0
    s_user = _bed({"travel_speed": 30, "wipe_speed": 25}, slow)
    assert s_user.travel_speed == 30.0
    assert s_user.wipe_speed == 25.0
    s_hi = _bed({"travel_speed": 80}, slow)
    assert s_hi.travel_speed == 40.0


def test_travel_speed_from_printer_user_override():
    fast = WipeKlipperHints(max_velocity=300.0)
    s = _bed({}, fast)
    assert s.travel_speed == 300.0
    s_user = _bed({"travel_speed": 150}, fast)
    assert s_user.travel_speed == 150.0
    s_none = _bed({}, WipeKlipperHints())
    assert s_none.travel_speed == 200.0


def test_fan_hint_none_skips_fan():
    s = _bed()
    assert s.fan is None
    s2 = _bed({}, WipeKlipperHints(fan="fan"))
    assert s2.fan == "fan"


def test_profiles_wipe_z_non_negative():
    assert _bed().wipe_z >= 0
    assert _rubber().wipe_z >= 0


def test_validate_negative_wipe_z():
    s = _rubber({"wipe_z": -0.1})
    result = validate_path(s)
    assert result.errors
    assert "wipe_z" in result.errors[0].message


def test_validate_travel_z_and_passes_and_fan():
    bad_z = validate_path(_rubber({"travel_z": 0.0, "wipe_z": 0.0}))
    assert any("travel_z" in e.message for e in bad_z.errors)
    bad_p = validate_path(_rubber({"passes": 0}))
    assert any("passes" in e.message for e in bad_p.errors)
    bad_f = validate_path(_rubber({"fan_speed": 1.5}))
    assert any("fan_speed" in e.message for e in bad_f.errors)


def test_validate_ok():
    assert validate_path(_bed()).errors == []


def test_validate_z_hop_negative():
    s = _bed({"z_hop": -0.1})
    result = validate_path(s)
    assert any("z_hop" in e.message for e in result.errors)


def test_validate_zero_length():
    s = _bed({"start_x": 1, "start_y": 1, "wipe_length": 0, "wipe_z": 0.2})
    result = validate_path(s)
    assert result.errors
    assert "start and end" in result.errors[0].message


def test_plan_wipe_actions_names():
    s = _bed({"retract": 0, "passes": 2})
    steps = plan_wipe_actions(s)
    assert [step.name for step in steps] == [
        "z_hop",
        "travel",
        "lower",
        "pass",
        "pass",
        "lift",
    ]
    assert steps[3].pass_index == 0
    assert steps[4].pass_index == 1
    assert len(steps[3].moves) == 2


def test_plan_wipe_actions_hold_z():
    s = _rubber({"retract": 0, "passes": 2})
    steps = plan_wipe_actions(s, hold_z=True)
    assert [step.name for step in steps] == ["travel", "pass", "pass"]
    assert all(move.z is None for step in steps for move in step.moves)
    moves = plan_wipe_moves(s, hold_z=True)
    assert moves[0].kind == MOVE_TRAVEL
    assert moves[0].x == s.start_x and moves[0].y == s.start_y
    assert moves[0].z is None
    assert all(m.z is None for m in moves)
    assert MOVE_LIFT not in [m.kind for m in moves]


def test_plan_wipe_moves_along_x():
    s = _rubber()
    assert s.passes == RUBBER_PASSES
    assert s.passes == 2
    moves = plan_wipe_moves(s)
    assert moves[0].kind == MOVE_TRAVEL
    assert moves[0].x is None and moves[0].y is None
    assert moves[0].z == s.z_hop
    assert moves[1].x == s.start_x
    assert moves[1].y == s.start_y
    assert moves[1].z == s.travel_z
    assert moves[2].z == RUBBER_WIPE_Z
    wipes = [m for m in moves if m.kind == MOVE_WIPE]
    assert len(wipes) == s.passes * 2
    assert wipes[0].x == s.start_x
    assert wipes[1].x == s.end_x
    assert moves[-1].kind == MOVE_LIFT


def test_plan_wipe_moves_along_y_and_offset():
    s = _rubber(
        {
            "start_x": 10,
            "start_y": 10,
            "end_x": 10,
            "end_y": 50,
            "passes": 3,
            "pass_offset": 2,
        }
    )
    moves = plan_wipe_moves(s)
    wipes = [m for m in moves if m.kind == MOVE_WIPE]
    assert wipes[0].y == 10
    assert wipes[1].y == 50
    assert wipes[2].x == 12


def test_plan_lifts_z_before_xy():
    s = _bed({"retract": 0})
    moves = plan_wipe_moves(s)
    assert moves[0].x is None and moves[0].y is None
    assert moves[0].z == s.z_hop
    assert moves[1].x == s.start_x and moves[1].y == s.start_y
    assert moves[1].z == s.travel_z
    assert moves[2].z == s.wipe_z


def test_rubber_box_spaces_passes_across_pad():
    s = _rubber(
        {
            "start_x": 100,
            "start_y": 200,
            "end_x": 140,
            "end_y": 220,
            "passes": 3,
            "pass_offset": 0,
        }
    )
    wipes = [m for m in plan_wipe_moves(s) if m.kind == MOVE_WIPE]
    ys = [m.y for m in wipes]
    assert ys[0] == 200.0
    assert ys[-1] == 220.0
    assert 210.0 in ys


def test_same_geometry_same_plan():
    shared = {
        "start_x": 1,
        "start_y": 2,
        "wipe_z": 0.2,
        "passes": 4,
        "pass_offset": 1,
        "wipe_speed": 80,
    }
    bed = _bed(dict(shared, wipe_length=40))
    rubber = _rubber(dict(shared, end_x=41, end_y=2))
    bmoves = plan_wipe_moves(bed)
    rmoves = plan_wipe_moves(rubber)
    assert [(m.x, m.y, m.z, m.speed, m.kind) for m in bmoves] == [
        (m.x, m.y, m.z, m.speed, m.kind) for m in rmoves
    ]


class _FakeReactor:
    def monotonic(self):
        return 0.0


class _FakePrinter:
    def __init__(self, objects):
        self._objects = objects

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)

    def lookup_objects(self, module=None):
        return list(self._objects.items())

    def add_object(self, name, obj):
        if name in self._objects:
            raise RuntimeError("Printer object '%s' already created" % (name,))
        self._objects[name] = obj

    def get_reactor(self):
        return _FakeReactor()


def test_hints_read_max_velocity_from_toolhead():
    class Toolhead:
        def get_max_velocity(self):
            return 250.0, 3000.0

    hints = collect_wipe_hints(_FakePrinter({"toolhead": Toolhead()}))
    assert hints.max_velocity == 250.0


class _PrinterConfig:
    def __init__(self, raw):
        self.status_raw_config = raw


class _Heater:
    min_extrude_temp = 190.0


class _Extruder:
    def get_heater(self):
        return _Heater()


def test_hints_z_hop_from_safe_z_home():
    class SafeZHome:
        z_hop = 3.0

    hints = collect_wipe_hints(_FakePrinter({"safe_z_home": SafeZHome()}))
    assert hints.z_hop == 3.0

    hints_missing = collect_wipe_hints(_FakePrinter({}))
    assert hints_missing.z_hop is None


def test_hints_min_extrude_temp_only_if_in_config():
    with_key = collect_wipe_hints(
        _FakePrinter(
            {
                "extruder": _Extruder(),
                "configfile": _PrinterConfig(
                    {"extruder": {"min_extrude_temp": "190"}}
                ),
            }
        )
    )
    assert with_key.min_nozzle_temp == 190.0 + MIN_EXTRUDE_TEMP_HEAT_MARGIN
    without_key = collect_wipe_hints(
        _FakePrinter(
            {
                "extruder": _Extruder(),
                "configfile": _PrinterConfig({"extruder": {}}),
            }
        )
    )
    assert without_key.min_nozzle_temp is None


class _FakeGcode:
    def __init__(self, fail_when=None):
        self.scripts = []
        self.fail_when = fail_when

    def register_command(self, name, func, desc=None):
        return None

    def run_script_from_command(self, script):
        self.scripts.append(script)
        if self.fail_when is not None and self.fail_when(script):
            raise RuntimeError("script failed: %s" % (script,))


class _FakeToolhead:
    def __init__(self, homed_axes="xyz"):
        self.homed_axes = homed_axes

    def get_status(self, eventtime):
        return {"homed_axes": self.homed_axes}


class _FakeGcmd:
    def error(self, text):
        raise RuntimeError(text)

    def respond_info(self, text):
        return None


class _FileConfig:
    def __init__(self, present):
        self.present = present

    def has_option(self, section, option):
        return (section, option) in self.present


class _FakeConfig:
    def __init__(self, printer):
        self._printer = printer
        self.fileconfig = _FileConfig(set())

    def get_printer(self):
        return self._printer

    def get_name(self):
        return "klipper_common wipe_nozzle_on_bed"


class _FakePauseResume:
    def __init__(self, is_paused):
        self.is_paused = is_paused

    def get_status(self, eventtime):
        return {"is_paused": self.is_paused}


class _WipePrinter(_FakePrinter):
    def __init__(self, gcode, homed_axes="xyz", is_paused=None):
        objects = {
            "gcode": gcode,
            "toolhead": _FakeToolhead(homed_axes),
        }
        if is_paused is not None:
            objects["pause_resume"] = _FakePauseResume(is_paused)
        super().__init__(objects)

    def register_event_handler(self, name, callback):
        return None


def _make_runner(spec, settings, gcode=None, is_paused=None, user=None):
    gcode = gcode or _FakeGcode()
    printer = _WipePrinter(gcode, is_paused=is_paused)
    runner = WipeRunner(_FakeConfig(printer), spec)
    runner.settings = settings
    if user is not None:
        runner._user = user
    return runner, gcode


def _script_index(scripts, prefix):
    for i, script in enumerate(scripts):
        if script.startswith(prefix) or script == prefix:
            return i
    raise AssertionError("no script starting with %r in %r" % (prefix, scripts))


def test_cmd_wipe_saves_then_restores_state():
    s = _bed({"retract": 0})
    runner, gcode = _make_runner(BED_SPEC, s)
    runner.cmd_wipe(_FakeGcmd())
    save = CMD_SAVE_GCODE_STATE % (BED_GCODE,)
    restore = CMD_RESTORE_GCODE_STATE % (BED_GCODE, s.travel_speed)
    assert gcode.scripts[0] == save
    assert restore == gcode.scripts[-1]
    assert "MOVE=1" in restore
    assert "MOVE_SPEED=%.0f" % (s.travel_speed,) in restore
    assert gcode.scripts[1] == CMD_ABSOLUTE
    lift_z = "G1 Z%.3f F%.0f" % (s.z_hop, s.travel_speed * 60.0)
    assert gcode.scripts[2] == lift_z
    assert "X" not in gcode.scripts[2]
    assert "Y" not in gcode.scripts[2]
    assert _script_index(gcode.scripts, save) < _script_index(gcode.scripts, "G1")
    assert gcode.scripts[-2] == lift_z
    assert gcode.scripts[-3] == CMD_ABSOLUTE


def test_cmd_wipe_restore_name_is_feature_gcode():
    bed_runner, bed_gcode = _make_runner(BED_SPEC, _bed({"retract": 0}))
    rubber_runner, rubber_gcode = _make_runner(RUBBER_SPEC, _rubber({"retract": 0}))
    bed_runner.cmd_wipe(_FakeGcmd())
    rubber_runner.cmd_wipe(_FakeGcmd())
    assert bed_gcode.scripts[0] == CMD_SAVE_GCODE_STATE % (BED_GCODE,)
    assert rubber_gcode.scripts[0] == CMD_SAVE_GCODE_STATE % (RUBBER_GCODE,)
    assert BED_GCODE in bed_gcode.scripts[-1]
    assert RUBBER_GCODE in rubber_gcode.scripts[-1]
    assert BED_GCODE not in rubber_gcode.scripts[-1]


def test_cmd_wipe_restores_state_on_error():
    s = _bed({"retract": 0})
    gcode = _FakeGcode(fail_when=lambda script: script.startswith("G1 X"))
    runner, gcode = _make_runner(BED_SPEC, s, gcode=gcode)
    with pytest.raises(RuntimeError, match="script failed"):
        runner.cmd_wipe(_FakeGcmd())
    assert gcode.scripts[0] == CMD_SAVE_GCODE_STATE % (BED_GCODE,)
    assert gcode.scripts[-1] == CMD_RESTORE_GCODE_STATE % (BED_GCODE, s.travel_speed)
    assert any(script.startswith("G1 X") for script in gcode.scripts)


def test_cmd_wipe_not_homed_does_not_save():
    gcode = _FakeGcode()
    printer = _WipePrinter(gcode, homed_axes="xy")
    runner = WipeRunner(_FakeConfig(printer), BED_SPEC)
    runner.settings = _bed({"retract": 0})
    with pytest.raises(RuntimeError, match="homed"):
        runner.cmd_wipe(_FakeGcmd())
    assert gcode.scripts == []


def test_cmd_wipe_bed_paused_does_not_save():
    runner, gcode = _make_runner(BED_SPEC, _bed({"retract": 0}), is_paused=True)
    with pytest.raises(RuntimeError, match="not allowed while paused"):
        runner.cmd_wipe(_FakeGcmd())
    assert gcode.scripts == []


def test_cmd_wipe_rubber_paused_xy_only_holds_z():
    s = _rubber({"retract": 0.5, "passes": 1, "nozzle_temperature": 220})
    runner, gcode = _make_runner(RUBBER_SPEC, s, is_paused=True)
    runner.cmd_wipe(_FakeGcmd())
    save = CMD_SAVE_GCODE_STATE % (RUBBER_GCODE,)
    restore = CMD_RESTORE_GCODE_STATE % (RUBBER_GCODE, s.travel_speed)
    assert gcode.scripts[0] == save
    assert gcode.scripts[-1] == restore
    lift_z = "G1 Z%.3f F%.0f" % (s.z_hop, s.travel_speed * 60.0)
    assert lift_z not in gcode.scripts
    assert not any(script.startswith("G1 Z") for script in gcode.scripts)
    assert any(script.startswith("G1 X") and "Z" not in script for script in gcode.scripts)
    assert not any("G1 E" in script or script.startswith("M109") for script in gcode.scripts)


@pytest.mark.parametrize("z_key", ("wipe_z", "z_hop", "travel_z"))
def test_cmd_wipe_rubber_paused_with_user_z_errors(z_key):
    s = _rubber({"retract": 0, z_key: 5})
    runner, gcode = _make_runner(
        RUBBER_SPEC, s, is_paused=True, user={z_key: "5"}
    )
    with pytest.raises(RuntimeError, match="with %s set" % (z_key,)):
        runner.cmd_wipe(_FakeGcmd())
    assert gcode.scripts == []


def test_cmd_wipe_rubber_not_paused_moves_z():
    s = _rubber({"retract": 0, "passes": 1})
    runner, gcode = _make_runner(RUBBER_SPEC, s, is_paused=False)
    runner.cmd_wipe(_FakeGcmd())
    lift_z = "G1 Z%.3f F%.0f" % (s.z_hop, s.travel_speed * 60.0)
    assert lift_z in gcode.scripts


def test_cmd_wipe_restore_failure_does_not_hide_wipe_error():
    s = _bed({"retract": 0})

    def fail_when(script):
        return script.startswith("G1 X") or script.startswith("RESTORE_GCODE_STATE")

    runner, _gcode = _make_runner(BED_SPEC, s, gcode=_FakeGcode(fail_when=fail_when))
    with pytest.raises(RuntimeError, match="G1 X"):
        runner.cmd_wipe(_FakeGcmd())


def test_cmd_wipe_lift_before_restore_failure_logs_warning(caplog):
    s = _bed({"retract": 0})
    gcode = _FakeGcode(fail_when=lambda script: script.startswith("G1 Z"))
    runner, _gcode = _make_runner(BED_SPEC, s, gcode=gcode)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError, match="G1 Z"):
            runner.cmd_wipe(_FakeGcmd())
    assert any("lift before restore" in r.getMessage() for r in caplog.records)


def test_cmd_wipe_fan_restore_failure_logs_warning(caplog):
    s = _bed({"retract": 0, "fan": "fan", "nozzle_temperature": 200})
    gcode = _FakeGcode(fail_when=lambda script: script.startswith("M106"))
    runner, _gcode = _make_runner(BED_SPEC, s, gcode=gcode)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError, match="M106"):
            runner.cmd_wipe(_FakeGcmd())
    assert any("restore fan" in r.getMessage() for r in caplog.records)


class _EmitTemplate:
    def __init__(self, line):
        self.line = line

    def render(self, context=None):
        extra = ""
        if context and "pass_index" in context:
            extra = " %s" % (context["pass_index"],)
        return self.line + extra


class _FakeCommonHook:
    def __init__(self, gcode):
        self.gcode = gcode

    def run_command_before(self, extra=None):
        self.gcode.run_script_from_command("COMMON_BEFORE")

    def run_command_after(self, extra=None):
        self.gcode.run_script_from_command("COMMON_AFTER")


def test_cmd_wipe_common_hooks_wrap():
    s = _bed({"retract": 0, "passes": 1})
    runner, gcode = _make_runner(BED_SPEC, s)
    runner.printer._objects["klipper_common hook"] = _FakeCommonHook(gcode)
    runner.cmd_wipe(_FakeGcmd())
    assert _script_index(gcode.scripts, "SAVE_GCODE_STATE") < _script_index(
        gcode.scripts, "COMMON_BEFORE"
    )
    assert _script_index(gcode.scripts, "COMMON_BEFORE") < _script_index(
        gcode.scripts, "G90"
    )
    assert _script_index(gcode.scripts, "COMMON_AFTER") < _script_index(
        gcode.scripts, "RESTORE_GCODE_STATE"
    )


def test_cmd_wipe_action_hooks_order():
    s = _bed({"retract": 0, "passes": 1})
    runner, gcode = _make_runner(BED_SPEC, s)
    runner._hook_templates[("z_hop", "before")] = _EmitTemplate("BEFORE_ZHOP")
    runner._hook_templates[("z_hop", "after")] = _EmitTemplate("AFTER_ZHOP")
    runner._hook_templates[("pass", "before")] = _EmitTemplate("BEFORE_PASS")
    runner._hook_templates[("pass", "after")] = _EmitTemplate("AFTER_PASS")
    runner.cmd_wipe(_FakeGcmd())
    assert _script_index(gcode.scripts, "SAVE_GCODE_STATE") < _script_index(
        gcode.scripts, "BEFORE_ZHOP"
    )
    assert _script_index(gcode.scripts, "BEFORE_ZHOP") < _script_index(
        gcode.scripts, "AFTER_ZHOP"
    )
    assert _script_index(gcode.scripts, "BEFORE_PASS") < _script_index(
        gcode.scripts, "AFTER_PASS"
    )
    assert _script_index(gcode.scripts, "AFTER_ZHOP") < _script_index(
        gcode.scripts, "BEFORE_PASS"
    )


def test_cmd_wipe_before_hook_stop_skips_work():
    s = _bed({"retract": 0})
    gcode = _FakeGcode()
    runner, gcode = _make_runner(BED_SPEC, s, gcode=gcode)
    gcode.fail_when = lambda script: script == "STOP_HOOK"

    class _FailTemplate:
        def render(self, context=None):
            return "STOP_HOOK"

    runner._hook_templates[("z_hop", "before")] = _FailTemplate()
    runner._on_hook_fail = "stop"
    printer = runner.printer
    printer.command_error = RuntimeError
    with pytest.raises(RuntimeError, match="script failed"):
        runner.cmd_wipe(_FakeGcmd())
    assert not any(script.startswith("G1 X") for script in gcode.scripts)
    assert gcode.scripts[-1].startswith("RESTORE_GCODE_STATE")


def test_cmd_wipe_skips_retract_and_fan_when_no_temp():
    s = _bed({"retract": 0.5, "fan": "fan"})
    assert s.min_nozzle_temp is None
    assert s.nozzle_temperature is None
    gcode = _FakeGcode()
    runner, _gcode = _make_runner(BED_SPEC, s, gcode=gcode)
    runner.cmd_wipe(_FakeGcmd())
    # No M106 (fan) or G1 E (retract) commands should be issued
    for script in gcode.scripts:
        assert not script.startswith("M106"), "fan should be skipped"
        assert not script.startswith("G1 E"), "retract should be skipped"
        assert not script.startswith("G91"), "retract relative mode should be skipped"
    # wipe motion commands (G1 X/Y/Z) should still be present
    assert any(
        script.startswith("G1") for script in gcode.scripts
    ), "wipe motion should still happen"
