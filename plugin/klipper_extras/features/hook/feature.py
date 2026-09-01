"""Klipper extra instance for [klipper_extras hook]."""

from __future__ import annotations

from ..base import FeatureBase
from .constants import (
    HOOK_ACTION_COMMAND,
    HOOK_PHASE_AFTER,
    HOOK_PHASE_BEFORE,
    KIND,
    OPTION_COMMAND_AFTER,
    OPTION_COMMAND_BEFORE,
)
from .execute import call_hook
from .load import load_debug, load_gcode_template, load_on_hook_fail


class CommonHook(FeatureBase):
    """Command-level before/after templates. No G-code command."""

    def __init__(self, config):
        super().__init__(config, kind=KIND)
        self.debug = load_debug(config)
        self._before = load_gcode_template(config, self.printer, OPTION_COMMAND_BEFORE)
        self._after = load_gcode_template(config, self.printer, OPTION_COMMAND_AFTER)
        self._on_hook_fail = load_on_hook_fail(config)

    def on_connect(self) -> None:
        pass

    def run_command_before(self, extra=None) -> None:
        extra = extra or {}
        kind = extra.get("kind", self.kind)
        call_hook(
            self.printer,
            self._before,
            self._on_hook_fail,
            kind,
            HOOK_ACTION_COMMAND,
            HOOK_PHASE_BEFORE,
            extra,
        )

    def run_command_after(self, extra=None) -> None:
        extra = extra or {}
        kind = extra.get("kind", self.kind)
        call_hook(
            self.printer,
            self._after,
            self._on_hook_fail,
            kind,
            HOOK_ACTION_COMMAND,
            HOOK_PHASE_AFTER,
            extra,
        )

    def get_status(self, eventtime):
        status = self.status_core()
        status["on_hook_fail"] = self._on_hook_fail
        status["debug"] = self.debug
        return status


def load_feature(config):
    return CommonHook(config)
