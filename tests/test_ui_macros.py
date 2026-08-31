"""Tests for Mainsail/Fluidd gcode_macro UI status objects."""

from __future__ import annotations

from klipper_common.features.ui_macros import (
    UiMacroShim,
    register_ui_macro_shims,
    ui_macro_object_name,
)


class _Printer:
    def __init__(self, existing=None):
        self._objects = dict(existing or {})
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


def test_register_adds_all_names():
    printer = _Printer()
    names = ("PAUSE", "WIPE_NOZZLE_ON_BED", "FORM_TIP")
    registered = register_ui_macro_shims(printer, names)
    assert registered == [
        "gcode_macro PAUSE",
        "gcode_macro WIPE_NOZZLE_ON_BED",
        "gcode_macro FORM_TIP",
    ]
    assert printer.added == registered
    for name in names:
        obj = printer.lookup_object(ui_macro_object_name(name))
        assert isinstance(obj, UiMacroShim)
        assert obj.get_status(0.0) == {}


def test_register_skips_existing_without_raise():
    existing = "gcode_macro PAUSE"
    printer = _Printer({existing: object()})
    registered = register_ui_macro_shims(printer, ("PAUSE", "RESUME"))
    assert registered == ["gcode_macro RESUME"]
    assert existing not in printer.added
    assert not isinstance(printer.lookup_object(existing), UiMacroShim)


def test_register_skips_existing_case_insensitive():
    printer = _Printer({"gcode_macro pause": object()})
    registered = register_ui_macro_shims(printer, ("PAUSE",))
    assert registered == []
    assert printer.added == []
