"""Tests for hook policy, execute helper, and common hook keys."""

from __future__ import annotations

import logging

import pytest

from klipper_common.constants import CONFIG_OPTION_KEYS
from klipper_common.features import FEATURE_GCODES, FEATURE_KINDS, FEATURE_LOADERS
from klipper_common.features.form_tip import OPTION_KEYS as FORM_TIP_KEYS
from klipper_common.features.form_tip.constants import FORM_TIP_HOOK_ACTIONS
from klipper_common.features.hook.constants import (
    DEFAULT_ON_HOOK_FAIL,
    KIND as HOOK_KIND,
    ON_FAIL_CONTINUE,
    ON_FAIL_STOP,
    OPTION_KEYS as HOOK_KEYS,
)
from klipper_common.features.hook.execute import (
    EmptyHookTemplate,
    bind_hooked,
    call_action_hook,
    call_common_hook,
    call_hook,
    run_hook_template,
    run_hooked_action,
)
from klipper_common.features.hook.messages import hook_debug_call
from klipper_common.features.hook.policy import (
    hook_option_keys_for_actions,
    is_hook_config_key,
    resolve_on_hook_fail,
)
from klipper_common.features.wipe_motion.constants import WIPE_HOOK_ACTIONS
from klipper_common.features.wipe_nozzle_on_bed import OPTION_KEYS as BED_KEYS
from klipper_common.features.wipe_nozzle_on_rubber import OPTION_KEYS as RUBBER_KEYS


class _FakeGcode:
    def __init__(self, fail=False):
        self.scripts = []
        self.infos = []
        self.fail = fail

    def run_script_from_command(self, script):
        self.scripts.append(script)
        if self.fail:
            raise RuntimeError("hook failed")

    def respond_info(self, text, log=True):
        self.infos.append(text)


class _FakePrinter:
    command_error = RuntimeError

    def __init__(self, gcode, hook=None):
        self._gcode = gcode
        self._hook = hook

    def lookup_object(self, name, default=None):
        if name == "gcode":
            return self._gcode
        if name == "klipper_common hook":
            return self._hook if self._hook is not None else default
        return default


class _ScriptTemplate:
    def __init__(self, script):
        self.script = script

    def render(self, context=None):
        return self.script


def test_hook_kind_in_registry_without_gcode():
    assert HOOK_KIND in FEATURE_KINDS
    assert HOOK_KIND in FEATURE_LOADERS
    assert HOOK_KIND not in FEATURE_GCODES
    assert HOOK_KEYS.isdisjoint(CONFIG_OPTION_KEYS)
    assert "command_before_gcode" in HOOK_KEYS
    assert "command_after_gcode" in HOOK_KEYS
    assert "on_hook_fail" in HOOK_KEYS
    assert "debug" in HOOK_KEYS


def test_resolve_on_hook_fail_default_stop():
    assert resolve_on_hook_fail(None) == ON_FAIL_STOP
    assert resolve_on_hook_fail("") == ON_FAIL_STOP
    assert resolve_on_hook_fail("  ") == DEFAULT_ON_HOOK_FAIL
    assert resolve_on_hook_fail("stop") == ON_FAIL_STOP
    assert resolve_on_hook_fail("CONTINUE") == ON_FAIL_CONTINUE


def test_resolve_on_hook_fail_unknown():
    with pytest.raises(ValueError, match="on_hook_fail"):
        resolve_on_hook_fail("abort")


def test_is_hook_config_key():
    assert is_hook_config_key("on_hook_fail")
    assert is_hook_config_key("before_pass_gcode")
    assert not is_hook_config_key("start_x")
    assert not is_hook_config_key("wipe_z")


def test_hook_option_keys_for_actions():
    keys = hook_option_keys_for_actions(("pass", "heat"))
    assert keys == frozenset(
        (
            "on_hook_fail",
            "before_pass_gcode",
            "after_pass_gcode",
            "before_heat_gcode",
            "after_heat_gcode",
        )
    )


def test_wipe_and_form_tip_own_hook_keys():
    for action in WIPE_HOOK_ACTIONS:
        before = "before_%s_gcode" % (action,)
        after = "after_%s_gcode" % (action,)
        assert before in BED_KEYS
        assert after in BED_KEYS
        assert before in RUBBER_KEYS
        assert after in RUBBER_KEYS
    assert "on_hook_fail" in BED_KEYS
    assert "on_hook_fail" in RUBBER_KEYS
    for action in FORM_TIP_HOOK_ACTIONS:
        assert "before_%s_gcode" % (action,) in FORM_TIP_KEYS
        assert "after_%s_gcode" % (action,) in FORM_TIP_KEYS
    assert "on_hook_fail" in FORM_TIP_KEYS
    assert "command_before_gcode" not in BED_KEYS
    assert "command_before_gcode" not in FORM_TIP_KEYS


def test_empty_template_is_noop():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    run_hook_template(
        printer, EmptyHookTemplate(), ON_FAIL_STOP, {}, "heat before"
    )
    assert gcode.scripts == []
    run_hook_template(
        printer, _ScriptTemplate("  \n"), ON_FAIL_STOP, {}, "heat before"
    )
    assert gcode.scripts == []


def test_run_hook_stop_reraises():
    gcode = _FakeGcode(fail=True)
    printer = _FakePrinter(gcode)
    with pytest.raises(RuntimeError, match="hook failed"):
        run_hook_template(
            printer,
            _ScriptTemplate("MY_MACRO"),
            ON_FAIL_STOP,
            {},
            "heat before",
        )
    assert gcode.scripts == ["MY_MACRO"]


def test_run_hook_continue_logs(caplog):
    gcode = _FakeGcode(fail=True)
    printer = _FakePrinter(gcode)
    with caplog.at_level(logging.WARNING):
        run_hook_template(
            printer,
            _ScriptTemplate("MY_MACRO"),
            ON_FAIL_CONTINUE,
            {},
            "heat before",
        )
    assert gcode.scripts == ["MY_MACRO"]
    assert any("on_hook_fail=continue" in r.getMessage() for r in caplog.records)


class _RaiseOnRender:
    def render(self, context=None):
        raise RuntimeError("action_raise_error")


def test_run_hook_continue_catches_render_command_error(caplog):
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    with caplog.at_level(logging.WARNING):
        run_hook_template(
            printer,
            _RaiseOnRender(),
            ON_FAIL_CONTINUE,
            {},
            "heat before",
        )
    assert gcode.scripts == []
    assert any("on_hook_fail=continue" in r.getMessage() for r in caplog.records)


def test_run_hook_stop_reraises_render_command_error():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    with pytest.raises(RuntimeError, match="action_raise_error"):
        run_hook_template(
            printer,
            _RaiseOnRender(),
            ON_FAIL_STOP,
            {},
            "heat before",
        )
    assert gcode.scripts == []


class _DebugHook:
    debug = True

    def __init__(self, printer, template):
        self.printer = printer
        self.template = template

    def run_command_before(self, extra=None):
        call_hook(
            self.printer,
            self.template,
            ON_FAIL_STOP,
            extra.get("kind") if extra else "hook",
            "command",
            "before",
            extra,
        )

    def run_command_after(self, extra=None):
        return None


def test_call_hook_debug_logs_before_run():
    gcode = _FakeGcode()
    hook = _DebugHook(None, _ScriptTemplate("MY_MACRO"))
    printer = _FakePrinter(gcode, hook=hook)
    hook.printer = printer
    call_hook(
        printer,
        _ScriptTemplate("MY_MACRO"),
        ON_FAIL_STOP,
        "wipe_nozzle_on_bed",
        "pass",
        "before",
        {"pass_index": 1},
    )
    assert gcode.infos == [
        hook_debug_call("wipe_nozzle_on_bed", "pass", "before", {"pass_index": 1})
    ]
    assert gcode.scripts == ["MY_MACRO"]


def test_call_hook_debug_logs_empty_template():
    gcode = _FakeGcode()
    hook = _DebugHook(None, EmptyHookTemplate())
    printer = _FakePrinter(gcode, hook=hook)
    hook.printer = printer
    call_hook(
        printer,
        EmptyHookTemplate(),
        ON_FAIL_STOP,
        "wipe_nozzle_on_bed",
        "z_hop",
        "before",
    )
    assert gcode.infos == [
        hook_debug_call("wipe_nozzle_on_bed", "z_hop", "before", empty=True)
    ]
    assert gcode.scripts == []


def test_call_hook_no_debug_is_silent():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    call_hook(
        printer,
        _ScriptTemplate("MY_MACRO"),
        ON_FAIL_STOP,
        "form_tip",
        "heat",
        "before",
    )
    assert gcode.infos == []
    assert gcode.scripts == ["MY_MACRO"]


def test_call_action_hook_uses_template_map():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    templates = {("pass", "before"): _ScriptTemplate("BEFORE_PASS")}
    call_action_hook(
        printer, templates, ON_FAIL_STOP, "wipe_nozzle_on_bed", "pass", "before"
    )
    assert gcode.scripts == ["BEFORE_PASS"]
    call_action_hook(
        printer, templates, ON_FAIL_STOP, "wipe_nozzle_on_bed", "pass", "after"
    )
    assert gcode.scripts == ["BEFORE_PASS"]


def test_call_common_hook_missing_is_noop():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    call_common_hook(printer, "before", {"kind": "form_tip"})
    assert gcode.scripts == []


def test_call_common_hook_debug_and_before():
    gcode = _FakeGcode()
    hook = _DebugHook(None, _ScriptTemplate("COMMON_BEFORE"))
    printer = _FakePrinter(gcode, hook=hook)
    hook.printer = printer
    call_common_hook(printer, "before", {"kind": "form_tip"})
    assert gcode.infos == [
        hook_debug_call("form_tip", "command", "before", {"kind": "form_tip"})
    ]
    assert gcode.scripts == ["COMMON_BEFORE"]


def test_bind_hooked_runs_before_work_after():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    templates = {
        ("fan", "before"): _ScriptTemplate("BEFORE"),
        ("fan", "after"): _ScriptTemplate("AFTER"),
    }
    hooked = bind_hooked(printer, templates, ON_FAIL_STOP, "form_tip")

    def work():
        gcode.scripts.append("WORK")

    hooked("fan", work)
    assert gcode.scripts == ["BEFORE", "WORK", "AFTER"]


def test_run_hooked_action_before_work_after():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    templates = {
        ("pass", "before"): _ScriptTemplate("BEFORE"),
        ("pass", "after"): _ScriptTemplate("AFTER"),
    }

    def work():
        gcode.scripts.append("WORK")
        return 3

    result = run_hooked_action(
        printer, templates, ON_FAIL_STOP, "wipe_nozzle_on_bed", "pass", work
    )
    assert result == 3
    assert gcode.scripts == ["BEFORE", "WORK", "AFTER"]


def test_run_hooked_action_skips_after_on_error():
    gcode = _FakeGcode()
    printer = _FakePrinter(gcode)
    templates = {
        ("pass", "before"): _ScriptTemplate("BEFORE"),
        ("pass", "after"): _ScriptTemplate("AFTER"),
    }

    def work():
        raise RuntimeError("work failed")

    with pytest.raises(RuntimeError, match="work failed"):
        run_hooked_action(
            printer, templates, ON_FAIL_STOP, "wipe_nozzle_on_bed", "pass", work
        )
    assert gcode.scripts == ["BEFORE"]

