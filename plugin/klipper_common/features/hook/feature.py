"""Klipper extra instance for [klipper_common hook]."""

from __future__ import annotations

from ... import messages as host_msg
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


class CommonHook:
    """Command-level before/after templates. No G-code command."""

    def __init__(self, config):
        self.printer = config.get_printer()
        self.kind = KIND
        self.debug = load_debug(config)
        self._before = load_gcode_template(config, self.printer, OPTION_COMMAND_BEFORE)
        self._after = load_gcode_template(config, self.printer, OPTION_COMMAND_AFTER)
        self._on_hook_fail = load_on_hook_fail(config)
        self.printer.register_event_handler("klippy:connect", self._handle_connect)

    def _handle_connect(self):
        host = self.printer.lookup_object("klipper_common", None)
        if host is None:
            raise self.printer.config_error(host_msg.feature_requires_host(self.kind))

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
        return {
            "kind": self.kind,
            "enabled": True,
            "on_hook_fail": self._on_hook_fail,
            "debug": self.debug,
        }


def load_feature(config):
    return CommonHook(config)
