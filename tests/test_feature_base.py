"""FeatureBase lifecycle (no Klipper tree)."""

import logging

import pytest

from klipper_extras.config_validate import ConfigIssue, ValidationResult
from klipper_extras.constants import CONFIG_SEVERITY_ERROR
from klipper_extras.features.base import FeatureBase
from klipper_extras.features.form_tip.feature import FormTipRunner
from klipper_extras.features.hook.feature import CommonHook
from klipper_extras.features.pause_resume.feature import PauseResumeRunner
from klipper_extras.features.purge_motion.runner import PurgeRunner
from klipper_extras.features.wipe_motion.runner import WipeRunner
from klipper_extras.messages import (
    config_validation_failed,
    fan_missing,
    feature_requires_host,
)


class _Gcode:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, func, desc=None):
        if func is None:
            self.commands.pop(name, None)
            return
        self.commands[name] = func


class _FileConfig:
    def has_option(self, section, option):
        return False


class _Printer:
    def __init__(self, objects):
        self._objects = objects
        self.config_error = ValueError
        self.added = []
        self.events = []

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
        self.events.append(name)


class _Config:
    def __init__(self, printer, section="klipper_extras form_tip"):
        self._printer = printer
        self.fileconfig = _FileConfig()
        self._section = section

    def get_printer(self):
        return self._printer

    def get_name(self):
        return self._section


class _Settings:
    fan = None


def _printer(with_host=True, extra=None):
    gcode = _Gcode()
    objects = {"gcode": gcode}
    if with_host:
        objects["klipper_extras"] = object()
    if extra:
        objects.update(extra)
    return _Printer(objects), gcode


class _OkFeature(FeatureBase):
    def __init__(self, config, **kwargs):
        super().__init__(config, kind="form_tip", **kwargs)

    def _command_bindings(self):
        return (("FORM_TIP", self._cmd, "help"),)

    def _cmd(self, gcmd):
        return None

    def resolve_settings(self):
        return _Settings()

    def validate_settings(self):
        return ValidationResult()


class _Hookish(FeatureBase):
    def __init__(self, config):
        super().__init__(config, kind="hook")
        self.did_connect = False
        self.did_ready = False

    def on_connect(self):
        self.did_connect = True

    def on_ready(self):
        self.did_ready = True


def test_prefix_extras_subclass_feature_base():
    assert issubclass(WipeRunner, FeatureBase)
    assert issubclass(PurgeRunner, FeatureBase)
    assert issubclass(FormTipRunner, FeatureBase)
    assert issubclass(PauseResumeRunner, FeatureBase)
    assert issubclass(CommonHook, FeatureBase)


def test_registers_connect_and_ready():
    printer, _gcode = _printer()
    _OkFeature(_Config(printer))
    assert printer.events == ["klippy:connect", "klippy:ready"]


def test_connect_requires_host():
    printer, _gcode = _printer(with_host=False)
    extra = _OkFeature(_Config(printer))
    with pytest.raises(ValueError, match=r"\[klipper_extras\]"):
        extra._handle_connect()
    assert "[klipper_extras]" in feature_requires_host("form_tip")


def test_connect_resolve_value_error_is_config_error():
    class _BadResolve(_OkFeature):
        def resolve_settings(self):
            raise ValueError("bad pose")

    printer, _gcode = _printer()
    extra = _BadResolve(_Config(printer))
    with pytest.raises(ValueError, match="bad pose"):
        extra._handle_connect()


def test_connect_validation_errors(caplog):
    class _BadValidate(_OkFeature):
        def validate_settings(self):
            result = ValidationResult()
            result.warnings.append(ConfigIssue("warning", "warn-me"))
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, "hard-fail")
            )
            return result

    printer, _gcode = _printer()
    extra = _BadValidate(_Config(printer))
    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError, match="hard-fail"):
            extra._handle_connect()
    assert "warn-me" in caplog.text
    assert "hard-fail" in config_validation_failed(["hard-fail"])


def test_connect_registers_ui_shims_and_commands():
    printer, gcode = _printer()
    extra = _OkFeature(_Config(printer))
    extra._handle_connect()
    assert "FORM_TIP" in gcode.commands
    assert "gcode_macro FORM_TIP" in printer.added
    assert extra.settings is not None


def test_hook_style_connect_skips_resolve_and_shims():
    printer, gcode = _printer()
    extra = _Hookish(_Config(printer, section="klipper_extras hook"))
    extra._handle_connect()
    extra._handle_ready()
    assert extra.did_connect is True
    assert extra.did_ready is True
    assert extra.settings is None
    assert gcode.commands == {}
    assert printer.added == []


def test_defer_commands_until_ready():
    class _Deferred(_OkFeature):
        def __init__(self, config):
            super().__init__(config, defer_commands=True)

        def on_ready(self):
            self._register_commands(replace=True)

    printer, gcode = _printer()
    extra = _Deferred(_Config(printer))
    assert gcode.commands == {}
    extra._handle_connect()
    assert gcode.commands == {}
    extra._handle_ready()
    assert "FORM_TIP" in gcode.commands


def test_connect_fan_object_missing():
    class _FanSettings:
        fan = "hotend_fan"

    class _WithFan(_OkFeature):
        def resolve_settings(self):
            return _FanSettings()

    printer, _gcode = _printer()
    extra = _WithFan(_Config(printer))
    with pytest.raises(ValueError, match="hotend_fan"):
        extra._handle_connect()
    assert "hotend_fan" in fan_missing("hotend_fan")


def test_required_components_missing():
    printer, _gcode = _printer()
    extra = _OkFeature(_Config(printer), required_components=("pause_resume",))
    with pytest.raises(ValueError, match="pause_resume"):
        extra._handle_connect()
