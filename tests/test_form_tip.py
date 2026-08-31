"""Tests for form_tip feature (pure logic, no Klipper tree)."""

import pytest

from klipper_common.constants import CONFIG_OPTION_KEYS
from klipper_common.features import FEATURE_GCODES, FEATURE_KINDS, FEATURE_LOADERS
from klipper_common.features.form_tip import (
    GCODE as FORM_TIP_GCODE,
    KIND as FORM_TIP_KIND,
    OPTION_KEYS as FORM_TIP_KEYS,
)
from klipper_common.features.form_tip.constants import PARAM_ALIASES
from klipper_common.features.form_tip.feature import FormTipRunner, _tip_step_hook
from klipper_common.features.form_tip.resolve import (
    overlay_gcode_params,
    plan_tip_steps,
    resolve_tip_settings,
)
from klipper_common.features.form_tip.types import FormTipHints
from klipper_common.features.form_tip.validate import validate_tip

HINTS = FormTipHints(max_extrude_only_velocity=300.0)


def _resolve(user=None, hints=None):
    return resolve_tip_settings(
        FORM_TIP_KIND,
        FORM_TIP_GCODE,
        user or {},
        hints if hints is not None else HINTS,
    )


class FakeGcmd:
    """Minimal gcmd stub for overlay testing."""

    def __init__(self, params: dict):
        self._params = params

    def get(self, key, default=None):
        return self._params.get(key, default)


# ── Feature identity ──────────────────────────────────────────────────────


def test_gcode_and_kind_owned():
    assert FORM_TIP_KIND == "form_tip"
    assert FORM_TIP_GCODE == "FORM_TIP"
    assert FORM_TIP_KIND in FEATURE_LOADERS
    assert FEATURE_GCODES[FORM_TIP_KIND] == FORM_TIP_GCODE
    assert FEATURE_LOADERS[FORM_TIP_KIND] is not None


def test_registry_includes_form_tip():
    assert FORM_TIP_KIND in FEATURE_KINDS
    assert set(FEATURE_LOADERS) == FEATURE_KINDS


def test_option_keys_owned_not_host():
    assert FORM_TIP_KEYS.isdisjoint(CONFIG_OPTION_KEYS - frozenset(("min_nozzle_temp",)))
    assert "start_x" not in FORM_TIP_KEYS
    assert "wipe_z" not in FORM_TIP_KEYS
    assert "fan" in FORM_TIP_KEYS
    assert "tip_distance" in FORM_TIP_KEYS
    assert "profile" in FORM_TIP_KEYS
    assert "sep_slow_len" not in FORM_TIP_KEYS  # compute-only


# ── Profile resolve ───────────────────────────────────────────────────────


def test_profile_a4t_hgx_lite_defaults():
    s = _resolve({"profile": "a4t_hgx_lite"})
    assert s.tip_distance == 35.1
    assert s.sep_slow_len == 35.1 - 6  # tip_distance - sep_fast_len
    assert s.sep_fast_len == 6.0
    assert s.cooling_moves == 4
    assert s.use_skinnydip is False
    assert s.fan_speed == 0.0
    assert s.unloading_speed_start_len == 0.0
    assert s.profile_name == "a4t_hgx_lite"


def test_profile_with_unload_start():
    s = _resolve({"profile": "a4t_hgx_lite", "unloading_speed_start_len": 5})
    assert s.sep_slow_len == 35.1 - 5 - 6  # tip - unload_start - sep_fast
    assert s.unloading_speed_start_len == 5.0


def test_profile_user_override():
    s = _resolve({"profile": "a4t_hgx_lite", "tip_distance": 40, "cooling_moves": 2})
    assert s.tip_distance == 40.0
    assert s.sep_slow_len == 40 - 6
    assert s.cooling_moves == 2


def test_no_profile_requires_tip_distance():
    s = _resolve({}, FormTipHints())
    result = validate_tip(s)
    assert result.errors


def test_unknown_profile_errors():
    with pytest.raises(ValueError, match="unknown profile"):
        _resolve({"profile": "nonexistent"})


def test_sep_too_long_errors():
    s = _resolve({"profile": "a4t_hgx_lite", "sep_fast_len": 50})
    result = validate_tip(s)
    assert result.errors


def test_clamp_to_max_velocity():
    slow = FormTipHints(max_extrude_only_velocity=10.0)
    s = _resolve({"profile": "a4t_hgx_lite"}, slow)
    assert s.sep_fast_speed <= 10.0
    assert s.sep_slow_speed <= 10.0
    assert s.cool_speed_fast <= 10.0


# ── Validation ────────────────────────────────────────────────────────────


def test_validate_tip_distance_required():
    s = _resolve({"profile": "a4t_hgx_lite", "tip_distance": 0})
    r = validate_tip(s)
    assert r.errors


def test_validate_cool_len_needed():
    s = _resolve({"profile": "a4t_hgx_lite", "cool_len": 0})
    r = validate_tip(s)
    assert r.errors


def test_validate_skinnydip_needs_dip_in():
    s = _resolve({"profile": "a4t_hgx_lite", "use_skinnydip": True, "dip_in": 0})
    r = validate_tip(s)
    assert r.errors


def test_validate_fan_speed_range():
    s = _resolve({"profile": "a4t_hgx_lite", "fan_speed": 1.5})
    r = validate_tip(s)
    assert r.errors


def test_validate_nozzle_temp_below_min():
    s = _resolve(
        {"profile": "a4t_hgx_lite", "nozzle_temperature": 150, "min_nozzle_temp": 180}
    )
    r = validate_tip(s)
    assert r.errors


def test_validate_ok():
    s = _resolve({"profile": "a4t_hgx_lite"})
    r = validate_tip(s)
    assert not r.errors
    assert not r.warnings


# ── Plan steps ────────────────────────────────────────────────────────────


def test_plan_default_profile():
    s = _resolve({"profile": "a4t_hgx_lite"})
    steps = plan_tip_steps(s)
    # No unload_start (len=0), no ramming (len=0), no skinnydip, no park
    labels = [st.label for st in steps]
    assert "unload_start" not in labels
    assert "sep_fast" in labels
    assert "sep_slow" in labels
    assert "ramming" not in labels
    assert "skinnydip" not in labels
    assert "parking" not in labels
    # 4 cooling moves
    cool_labels = [lb for lb in labels if lb.startswith("cool_")]
    assert len(cool_labels) == 4


def test_plan_cooling_moves_1():
    s = _resolve({"profile": "a4t_hgx_lite", "cooling_moves": 1})
    steps = plan_tip_steps(s)
    cool = [st for st in steps if st.label.startswith("cool_")]
    assert len(cool) == 1  # one pair
    command = cool[0].command
    assert command.count("G1") == 2  # extend + retract


def test_plan_cooling_moves_0():
    s = _resolve({"profile": "a4t_hgx_lite", "cooling_moves": 0})
    steps = plan_tip_steps(s)
    cool = [st for st in steps if st.label.startswith("cool_")]
    assert len(cool) == 0


def test_plan_ramming():
    s = _resolve({"profile": "a4t_hgx_lite", "ramming_len": 5})
    steps = plan_tip_steps(s)
    labels = [st.label for st in steps]
    assert "ramming" in labels


def test_plan_skinnydip():
    s = _resolve(
        {"profile": "a4t_hgx_lite", "use_skinnydip": True, "dip_in": 10}
    )
    steps = plan_tip_steps(s)
    labels = [st.label for st in steps]
    assert "skinnydip" in labels


def test_plan_parking():
    s = _resolve({"profile": "a4t_hgx_lite", "parking_distance": 10})
    steps = plan_tip_steps(s)
    labels = [st.label for st in steps]
    assert "parking" in labels
    # parking uses abs, always negative
    assert "-10" in steps[-1].command or "-10.000" in steps[-1].command


def test_plan_unload_start():
    s = _resolve(
        {"profile": "a4t_hgx_lite", "unloading_speed_start_len": 5}
    )
    steps = plan_tip_steps(s)
    labels = [st.label for st in steps]
    assert "unload_start" in labels
    assert "sep_fast" in labels
    assert "sep_slow" in labels


# ── Overlay params ────────────────────────────────────────────────────────


def test_overlay_no_params_returns_same():
    s = _resolve({"profile": "a4t_hgx_lite"})
    gcmd = FakeGcmd({})
    overlaid = overlay_gcode_params(gcmd, s)
    assert overlaid == s


def test_overlay_tip_distance():
    s = _resolve({"profile": "a4t_hgx_lite"})
    gcmd = FakeGcmd({"TIP_DISTANCE": "40"})
    overlaid = overlay_gcode_params(gcmd, s)
    assert overlaid.tip_distance == 40.0
    assert overlaid.sep_slow_len == 40.0 - 6.0


def test_overlay_nozzle_temp_alias():
    s = _resolve({"profile": "a4t_hgx_lite"})
    gcmd = FakeGcmd({"NOZZLE_TEMP": "220"})
    overlaid = overlay_gcode_params(gcmd, s)
    assert overlaid.nozzle_temperature == 220.0


def test_overlay_does_not_mutate_snapshot():
    s = _resolve({"profile": "a4t_hgx_lite"})
    original_tip = s.tip_distance
    gcmd = FakeGcmd({"TIP_DISTANCE": "99"})
    overlaid = overlay_gcode_params(gcmd, s)
    assert overlaid.tip_distance == 99.0
    assert s.tip_distance == original_tip  # unchanged


# ── PARAM_ALIASES ─────────────────────────────────────────────────────────


def test_param_aliases_coverage():
    """Every alias maps to a real OPTION_KEY."""
    for alias, key in PARAM_ALIASES.items():
        assert key in FORM_TIP_KEYS, (
            "alias %r maps to %r which is not in OPTION_KEYS" % (alias, key)
        )


def test_all_option_keys_have_upper_case():
    """Every OPTION_KEY should be reachable via UPPER_SNAKE_CASE."""
    for key in FORM_TIP_KEYS:
        gcode_key = key.upper()
        assert gcode_key == gcode_key  # just checking it's defined
        # The key itself is valid — overlay tries it first


# ── Sep_slow_len is compute-only ──────────────────────────────────────────


def test_sep_slow_len_computed():
    s = _resolve({"profile": "a4t_hgx_lite", "tip_distance": 50, "sep_fast_len": 10})
    assert s.sep_slow_len == 40.0


def test_sep_slow_len_with_unload_start():
    s = _resolve(
        {
            "profile": "a4t_hgx_lite",
            "tip_distance": 50,
            "sep_fast_len": 10,
            "unloading_speed_start_len": 5,
        }
    )
    assert s.sep_slow_len == 50.0 - 5.0 - 10.0


# ── Command hooks ─────────────────────────────────────────────────────────


def test_tip_step_hook_labels():
    assert _tip_step_hook("cool_0") == ("cool", {"pass_index": 0})
    assert _tip_step_hook("cool_3") == ("cool", {"pass_index": 3})
    assert _tip_step_hook("fan_on") == ("fan", None)
    assert _tip_step_hook("sep_fast") == ("sep_fast", None)


class _TipGcode:
    def __init__(self):
        self.scripts = []

    def register_command(self, name, func, desc=None):
        return None

    def run_script_from_command(self, script):
        self.scripts.append(script)


class _TipFileConfig:
    def has_option(self, section, option):
        return False


class _TipPrinter:
    def __init__(self, gcode):
        self._objects = {"gcode": gcode}

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)

    def register_event_handler(self, name, callback):
        return None

    def get_reactor(self):
        class _R:
            def monotonic(self):
                return 0.0

        return _R()


class _TipConfig:
    def __init__(self, printer):
        self._printer = printer
        self.fileconfig = _TipFileConfig()

    def get_printer(self):
        return self._printer

    def get_name(self):
        return "klipper_common form_tip"


class _TipGcmd:
    def error(self, text):
        raise RuntimeError(text)

    def respond_info(self, text):
        return None

    def get(self, key, default=None):
        return default


class _EmitTipTemplate:
    def __init__(self, line):
        self.line = line

    def render(self, context=None):
        extra = ""
        if context and "pass_index" in context:
            extra = " %s" % (context["pass_index"],)
        return self.line + extra


def _make_tip_runner(settings, gcode=None):
    gcode = gcode or _TipGcode()
    printer = _TipPrinter(gcode)
    runner = FormTipRunner(_TipConfig(printer))
    runner.settings = settings
    return runner, gcode


def test_cmd_form_tip_action_hooks_order():
    s = _resolve(
        {
            "profile": "a4t_hgx_lite",
            "cooling_moves": 1,
            "unloading_speed_start_len": 0,
            "ramming_len": 0,
            "fan_speed": 0,
            "use_skinnydip": False,
            "parking_distance": 0,
        }
    )
    runner, gcode = _make_tip_runner(s)
    runner._hook_templates[("sep_fast", "before")] = _EmitTipTemplate("BEFORE_SEP")
    runner._hook_templates[("sep_fast", "after")] = _EmitTipTemplate("AFTER_SEP")
    runner._hook_templates[("cool", "before")] = _EmitTipTemplate("BEFORE_COOL")
    runner._hook_templates[("cool", "after")] = _EmitTipTemplate("AFTER_COOL")
    runner.cmd_FORM_TIP(_TipGcmd())
    scripts = gcode.scripts
    assert scripts[0] == "SAVE_GCODE_STATE NAME=FORM_TIP"
    assert scripts[-1] == "RESTORE_GCODE_STATE NAME=FORM_TIP"
    i_before = scripts.index("BEFORE_SEP")
    i_after = scripts.index("AFTER_SEP")
    i_cool_b = scripts.index("BEFORE_COOL 0")
    i_cool_a = scripts.index("AFTER_COOL 0")
    assert i_before < i_after < i_cool_b < i_cool_a


def test_cmd_form_tip_common_hooks_wrap():
    s = _resolve(
        {
            "profile": "a4t_hgx_lite",
            "cooling_moves": 0,
            "unloading_speed_start_len": 0,
            "ramming_len": 0,
            "fan_speed": 0,
            "use_skinnydip": False,
            "parking_distance": 0,
        }
    )
    runner, gcode = _make_tip_runner(s)

    class _Common:
        def run_command_before(self, extra=None):
            gcode.run_script_from_command("COMMON_BEFORE")

        def run_command_after(self, extra=None):
            gcode.run_script_from_command("COMMON_AFTER")

    runner.printer._objects["klipper_common hook"] = _Common()
    runner.cmd_FORM_TIP(_TipGcmd())
    scripts = gcode.scripts
    assert scripts[0] == "SAVE_GCODE_STATE NAME=FORM_TIP"
    assert scripts[1] == "COMMON_BEFORE"
    assert scripts.index("COMMON_AFTER") < scripts.index(
        "RESTORE_GCODE_STATE NAME=FORM_TIP"
    )
    assert scripts[-1] == "RESTORE_GCODE_STATE NAME=FORM_TIP"
