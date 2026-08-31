import logging
import math
import re
from pathlib import Path

import pytest

from klipper_common.features.purge_at_pose.constants import (
    GCODE as POSE_GCODE,
    KIND as POSE_KIND,
    OPTION_KEYS as POSE_KEYS,
    SPEC as POSE_SPEC,
)
from klipper_common.features.purge_motion.constants import (
    BREAK_TRAVEL,
    DEFAULT_TRAVEL_Z,
    ORIGIN_ADAPTIVE,
    ORIGIN_FIXED,
)
from klipper_common.features.purge_motion.hints import (
    host_min_nozzle_temp_from_host,
)
from klipper_common.features.purge_motion.messages import leveling_not_applied
from klipper_common.features.purge_motion.resolve import (
    e_speed_mms,
    heat_wait_target,
    overlay_purge_amount,
    plan_purge_actions,
    resolve_bed_origin,
)
from klipper_common.features.purge_motion.runner import (
    PurgeRunner,
    unset_leveling_commands,
)
from klipper_common.features.purge_motion.styles import VORON_STROKES, voron_strokes
from klipper_common.features.purge_motion.types import PurgeKlipperHints
from klipper_common.features.purge_motion.validate import validate_path
from klipper_common.features.purge_on_bed.constants import (
    GCODE as PURGE_BED_GCODE,
    KIND as PURGE_BED_KIND,
    OPTION_KEYS as PURGE_BED_KEYS,
    SPEC as PURGE_BED_SPEC,
)

ROOT = Path(__file__).resolve().parents[1]
HINTS = PurgeKlipperHints(
    filament_diameter=1.75, max_velocity=300.0, min_nozzle_temp=180.0
)
POSE_XY = {"start_x": 10, "start_y": 20, "purge_z": 2}


def _bed(user=None, hints=None):
    return PURGE_BED_SPEC.resolve(user or {}, hints if hints is not None else HINTS)


def _pose(user=None, hints=None):
    data = dict(POSE_XY)
    if user:
        data.update(user)
    return POSE_SPEC.resolve(data, hints if hints is not None else HINTS)


def _names(steps):
    return [step.name for step in steps]


def test_gcode_and_kind_owned():
    assert PURGE_BED_SPEC.kind == PURGE_BED_KIND
    assert POSE_SPEC.kind == POSE_KIND
    assert PURGE_BED_SPEC.gcode == PURGE_BED_GCODE
    assert POSE_SPEC.gcode == POSE_GCODE
    assert PURGE_BED_SPEC.gcode != POSE_SPEC.gcode


def test_filament_diameter_required():
    with pytest.raises(ValueError, match="filament_diameter"):
        _bed({}, PurgeKlipperHints())


def test_pose_requires_xy_and_purge_z():
    with pytest.raises(ValueError, match="start_x"):
        POSE_SPEC.resolve({}, HINTS)
    with pytest.raises(ValueError, match="purge_z"):
        POSE_SPEC.resolve({"start_x": 1, "start_y": 2}, HINTS)


def test_bed_partial_xy_errors():
    with pytest.raises(ValueError, match="both start_x"):
        _bed({"start_x": 10})
    with pytest.raises(ValueError, match="both start_x"):
        _bed({"start_y": 10})


def test_bed_fixed_origin_skips_aabb():
    s = _bed({"start_x": 12, "start_y": 34})
    assert s.origin_mode == ORIGIN_FIXED
    assert s.start_x == 12.0
    assert s.start_y == 34.0
    ox, oy = resolve_bed_origin(s, (0, 0, 100, 100))
    assert (ox, oy) == (12.0, 34.0)


def test_bed_adaptive_origin_line_and_voron():
    s = _bed({})
    assert s.origin_mode == ORIGIN_ADAPTIVE
    assert s.start_x is None
    aabb = (40.0, 50.0, 80.0, 90.0)
    ox, oy = resolve_bed_origin(s, aabb)
    length = s.purge_length
    assert ox == pytest.approx(((40 + 80) / 2) - length / 2)
    assert oy == pytest.approx(50.0 - s.purge_margin)
    with pytest.raises(ValueError, match="exclude_object"):
        resolve_bed_origin(s, None)
    v = _bed({"style": "voron"})
    vox, voy = resolve_bed_origin(v, aabb)
    assert (vox, voy) == (40.0 - v.purge_margin, 50.0 - v.purge_margin)


def test_along_voron_and_style_size_line_conflict():
    with pytest.raises(ValueError, match="along"):
        _bed({"style": "voron", "along": "x"})
    with pytest.raises(ValueError, match="style_size"):
        _bed({"style": "line", "style_size": 12})
    with pytest.raises(ValueError, match="purge_length"):
        _bed({"style": "voron", "purge_length": 30})


def test_unknown_style():
    with pytest.raises(ValueError, match="unknown style"):
        _bed({"style": "icon"})


def test_heat_temp_required_when_missing():
    hints = PurgeKlipperHints(filament_diameter=1.75)
    with pytest.raises(ValueError, match="nozzle temperature"):
        _bed({}, hints)
    s = _bed({"nozzle_temperature": 220}, hints)
    assert s.nozzle_temperature == 220.0
    assert s.min_nozzle_temp is None


def test_host_min_nozzle_temp_before_host_connect():
    pending = type("Host", (), {"settings": None, "_user": None})()
    pending._user = {"min_nozzle_temp": "200"}
    assert host_min_nozzle_temp_from_host(pending) == 200.0
    assert host_min_nozzle_temp_from_host(None) is None
    resolved = type("Host", (), {"settings": None, "_user": None})()
    resolved.settings = type("S", (), {"min_nozzle_temp": 210.0})()
    resolved._user = {"min_nozzle_temp": "200"}
    assert host_min_nozzle_temp_from_host(resolved) == 210.0


def test_heat_wait_target_heats_to_floor_when_cold():
    assert heat_wait_target(220.0, 180.0, 25.0, 0.0) == 220.0
    assert heat_wait_target(None, 180.0, 190.0, 0.0) is None
    assert heat_wait_target(None, 180.0, 25.0, 200.0) == 200.0
    assert heat_wait_target(None, 180.0, 25.0, 0.0) == 180.0


def test_min_nozzle_temp_purge_beats_host_beats_extruder():
    hints = PurgeKlipperHints(
        filament_diameter=1.75,
        min_nozzle_temp=170.0,
        host_min_nozzle_temp=190.0,
    )
    assert _bed({}, hints).min_nozzle_temp == 190.0
    assert _bed({"min_nozzle_temp": 210}, hints).min_nozzle_temp == 210.0
    only_extruder = PurgeKlipperHints(
        filament_diameter=1.75, min_nozzle_temp=170.0
    )
    assert _bed({}, only_extruder).min_nozzle_temp == 170.0


def test_travel_z_not_from_z_hop():
    hints = PurgeKlipperHints(
        filament_diameter=1.75, min_nozzle_temp=180.0, z_hop=0.5
    )
    s = _bed({}, hints)
    assert s.z_hop == 0.5
    assert s.travel_z == DEFAULT_TRAVEL_Z
    assert s.travel_z > s.purge_z


def test_user_beats_hint_beats_profile():
    hints = PurgeKlipperHints(
        filament_diameter=1.75,
        min_nozzle_temp=180.0,
        retract=1.2,
        max_velocity=300.0,
    )
    s = _bed({"min_nozzle_temp": 200, "retract": 0.3, "purge_z": 0.4}, hints)
    assert s.min_nozzle_temp == 200.0
    assert s.retract == 0.3
    assert s.purge_z == 0.4
    s2 = _bed({}, hints)
    assert s2.min_nozzle_temp == 180.0
    assert s2.retract == 1.2
    assert s2.travel_speed == 300.0
    s_user_speed = _bed({"travel_speed": 150}, hints)
    assert s_user_speed.travel_speed == 150.0


def test_line_plan_has_one_purge_and_break():
    s = _bed({"start_x": 10, "start_y": 20, "purge_length": 30, "retract": 0})
    steps = plan_purge_actions(s)
    names = _names(steps)
    assert names.count("purge") == 1
    assert "break" in names
    assert "recover" not in names
    purge = next(st for st in steps if st.name == "purge")
    move = purge.moves[0]
    assert move.x == pytest.approx(40.0)
    assert move.y == pytest.approx(20.0)
    assert move.e == pytest.approx(s.purge_amount)
    brk = next(st for st in steps if st.name == "break")
    assert brk.moves[0].x == pytest.approx(40.0 + BREAK_TRAVEL)


def test_voron_plan_three_purges_recover_no_break():
    s = _bed({"start_x": 0, "start_y": 0, "style": "voron", "retract": 0.5})
    steps = plan_purge_actions(s)
    names = _names(steps)
    assert names.count("purge") == 3
    assert names.count("recover") == 2
    assert "break" not in names
    purges = [st for st in steps if st.name == "purge"]
    expected = voron_strokes(0.0, 0.0, 10.0)
    for i, (st, stroke) in enumerate(zip(purges, expected)):
        assert st.pass_index == i
        assert st.moves[0].x == pytest.approx(stroke.end_x)
        assert st.moves[0].y == pytest.approx(stroke.end_y)
        assert st.moves[0].e == pytest.approx(s.purge_amount * stroke.e_fraction)


def test_voron_offsets_match_kamp():
    strokes = voron_strokes(0.0, 0.0, 10.0)
    assert len(strokes) == 3
    for stroke, ((sx, sy), (ex, ey), frac) in zip(strokes, VORON_STROKES):
        assert stroke.start_x == pytest.approx(sx * 10)
        assert stroke.start_y == pytest.approx(sy * 10)
        assert stroke.end_x == pytest.approx(ex * 10)
        assert stroke.end_y == pytest.approx(ey * 10)
        assert stroke.e_fraction == frac


def test_pose_plan_e_only_no_break():
    s = _pose()
    steps = plan_purge_actions(s)
    names = _names(steps)
    assert "break" not in names
    assert "recover" not in names
    purge = next(st for st in steps if st.name == "purge")
    move = purge.moves[0]
    assert move.x is None
    assert move.y is None
    assert move.e == pytest.approx(s.purge_amount)


def test_e_speed_from_diameter_not_kamp_div5():
    speed = e_speed_mms(12.0, 1.75)
    kamp = 12.0 / 5.0
    assert speed != pytest.approx(kamp)
    area = math.pi * (1.75 / 2.0) ** 2
    assert speed == pytest.approx(12.0 / area)


def test_overlay_purge_amount_does_not_mutate():
    s = _bed({"start_x": 1, "start_y": 2, "purge_amount": 30})
    s2 = overlay_purge_amount(s, 12)
    assert s.purge_amount == 30.0
    assert s2.purge_amount == 12.0
    assert overlay_purge_amount(s, None) is s


def test_validate_travel_z():
    s = _pose({"purge_z": 2, "travel_z": 1})
    result = validate_path(s)
    assert result.errors


def test_out_of_range_errors():
    hints = PurgeKlipperHints(
        filament_diameter=1.75,
        min_nozzle_temp=180.0,
        axis_maximum_x=50.0,
        axis_minimum_x=0.0,
        axis_maximum_y=50.0,
        axis_minimum_y=0.0,
    )
    s = _bed(
        {"start_x": 40, "start_y": 10, "purge_length": 20, "retract": 0},
        hints,
    )
    with pytest.raises(ValueError, match="need"):
        plan_purge_actions(s)


def test_sample_and_docs_keys_subset():
    for kind, keys, sample, doc in (
        (
            "purge_on_bed",
            PURGE_BED_KEYS,
            ROOT / "config" / "sample-purge-on-bed.cfg",
            ROOT / "docs" / "features" / "purge_on_bed.md",
        ),
        (
            "purge_at_pose",
            POSE_KEYS,
            ROOT / "config" / "sample-purge-at-pose.cfg",
            ROOT / "docs" / "features" / "purge_at_pose.md",
        ),
    ):
        text = sample.read_text(encoding="utf-8")
        found = set(re.findall(r"^#?\s*([a-z][a-z0-9_]*)\s*:", text, re.M))
        extra = found - keys
        assert not extra, "%s sample extra keys %s" % (kind, extra)
        doc_text = doc.read_text(encoding="utf-8")
        assert kind.replace("_", " ") in doc_text.lower() or kind in doc_text
        assert "QUAD_GANTRY_LEVEL" in doc_text
        assert "Z_TILT_ADJUST" in doc_text


class _LevelObj:
    def __init__(self, applied):
        self.applied = applied

    def get_status(self, eventtime):
        return {"applied": self.applied}


class _LookupPrinter:
    def __init__(self, objects):
        self._objects = objects

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)


def test_unset_leveling_commands():
    assert unset_leveling_commands(_LookupPrinter({}), 0.0) == []
    assert (
        unset_leveling_commands(
            _LookupPrinter({"quad_gantry_level": _LevelObj(True)}), 0.0
        )
        == []
    )
    assert unset_leveling_commands(
        _LookupPrinter({"quad_gantry_level": _LevelObj(False)}), 0.0
    ) == ["QUAD_GANTRY_LEVEL"]
    assert unset_leveling_commands(
        _LookupPrinter({"z_tilt": _LevelObj(False)}), 0.0
    ) == ["Z_TILT_ADJUST"]
    assert unset_leveling_commands(
        _LookupPrinter(
            {
                "quad_gantry_level": _LevelObj(False),
                "z_tilt": _LevelObj(False),
            }
        ),
        0.0,
    ) == ["QUAD_GANTRY_LEVEL", "Z_TILT_ADJUST"]


class _FakeReactor:
    def monotonic(self):
        return 0.0


class _FakeGcode:
    def __init__(self):
        self.scripts = []

    def register_command(self, name, func, desc=None):
        return None

    def run_script_from_command(self, script):
        self.scripts.append(script)


class _FakeToolhead:
    def __init__(self, homed_axes="xyz"):
        self.homed_axes = homed_axes

    def get_status(self, eventtime):
        return {"homed_axes": self.homed_axes}


class _FakeGcmd:
    def __init__(self):
        self.infos = []

    def error(self, text):
        raise RuntimeError(text)

    def respond_info(self, text):
        self.infos.append(text)

    def get_float(self, name, default=None):
        return default


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
        return "klipper_common purge_at_pose"


class _PurgePrinter:
    def __init__(self, gcode, extra=None, homed_axes="xyz"):
        self._objects = {
            "gcode": gcode,
            "toolhead": _FakeToolhead(homed_axes),
        }
        if extra:
            self._objects.update(extra)

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)

    def get_reactor(self):
        return _FakeReactor()

    def register_event_handler(self, name, callback):
        return None


def _make_pose_runner(gcode=None, extra=None):
    gcode = gcode or _FakeGcode()
    printer = _PurgePrinter(gcode, extra=extra)
    runner = PurgeRunner(_FakeConfig(printer), POSE_SPEC)
    runner.settings = _pose({"retract": 0, "nozzle_temperature": 200})
    return runner, gcode


def test_cmd_purge_warns_when_qgl_not_applied(caplog):
    runner, gcode = _make_pose_runner(
        extra={"quad_gantry_level": _LevelObj(False)}
    )
    gcmd = _FakeGcmd()
    with caplog.at_level(logging.WARNING):
        runner.cmd_purge(gcmd)
    text = leveling_not_applied("QUAD_GANTRY_LEVEL")
    assert gcmd.infos == [text]
    assert any(text in r.getMessage() for r in caplog.records)
    assert gcode.scripts[0].startswith("SAVE_GCODE_STATE")


def test_cmd_purge_warns_when_z_tilt_not_applied():
    runner, gcode = _make_pose_runner(extra={"z_tilt": _LevelObj(False)})
    gcmd = _FakeGcmd()
    runner.cmd_purge(gcmd)
    assert gcmd.infos == [leveling_not_applied("Z_TILT_ADJUST")]
    assert gcode.scripts[0].startswith("SAVE_GCODE_STATE")


def test_cmd_purge_no_warn_when_leveling_applied_or_absent():
    runner, _gcode = _make_pose_runner()
    gcmd = _FakeGcmd()
    runner.cmd_purge(gcmd)
    assert gcmd.infos == []
    runner, _gcode = _make_pose_runner(
        extra={"quad_gantry_level": _LevelObj(True)}
    )
    gcmd = _FakeGcmd()
    runner.cmd_purge(gcmd)
    assert gcmd.infos == []


def test_cmd_purge_not_homed_skips_leveling_warn():
    gcode = _FakeGcode()
    printer = _PurgePrinter(
        gcode, extra={"z_tilt": _LevelObj(False)}, homed_axes="xy"
    )
    runner = PurgeRunner(_FakeConfig(printer), POSE_SPEC)
    runner.settings = _pose({"retract": 0, "nozzle_temperature": 200})
    gcmd = _FakeGcmd()
    with pytest.raises(RuntimeError, match="homed"):
        runner.cmd_purge(gcmd)
    assert gcmd.infos == []
    assert gcode.scripts == []
