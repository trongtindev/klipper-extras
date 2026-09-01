"""Host component checks (no Klipper tree)."""

import logging

import pytest

from klipper_extras.components import (
    check_components,
    ensure_feature_components,
    lookup_component,
    missing_components,
)
from klipper_extras.messages import (
    component_optional_missing,
    components_required_missing,
    feature_requires_host,
)


class _Printer:
    def __init__(self, objects):
        self._objects = objects
        self.config_error = ValueError

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)


def test_lookup_and_missing_order():
    printer = _Printer({"a": object()})
    assert lookup_component(printer, "a") is printer._objects["a"]
    assert missing_components(printer, ("a", "b", "c")) == ["b", "c"]


def test_required_missing_raises():
    printer = _Printer({})
    with pytest.raises(ValueError, match="pause_resume"):
        check_components(
            printer, "pause_resume", required=("virtual_sdcard", "pause_resume")
        )
    err = components_required_missing("pause_resume", ["virtual_sdcard", "pause_resume"])
    assert "virtual_sdcard" in err
    assert "pause_resume" in err


def test_optional_missing_warns(caplog):
    printer = _Printer({"need": object()})
    with caplog.at_level(logging.WARNING):
        found = check_components(
            printer, "pause_resume", required=("need",), optional=("idle_timeout",)
        )
    assert found["need"] is printer._objects["need"]
    assert found["idle_timeout"] is None
    assert "idle_timeout" in caplog.text
    assert "pause_resume" in component_optional_missing("pause_resume", "idle_timeout")


def test_ensure_requires_host():
    printer = _Printer({})
    with pytest.raises(ValueError, match=r"\[klipper_extras\]"):
        ensure_feature_components(printer, "form_tip")
    assert "[klipper_extras]" in feature_requires_host("form_tip")


def test_ensure_with_host_empty_required():
    host = object()
    printer = _Printer({"klipper_extras": host})
    assert ensure_feature_components(printer, "form_tip") == {}


def test_ensure_required_missing_is_config_error():
    printer = _Printer({"klipper_extras": object()})
    with pytest.raises(ValueError, match="requires Klipper extra"):
        ensure_feature_components(
            printer, "pause_resume", required=("virtual_sdcard", "pause_resume", "respond")
        )
