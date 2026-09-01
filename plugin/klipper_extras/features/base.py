"""Shared Klipper lifecycle for one ``[klipper_extras <kind>]`` extra.

Prefix extras subclass ``FeatureBase``. The host ``[klipper_extras]`` object
does not. No feature option keys, G-code names, or geometry live here.
"""

from __future__ import annotations

import logging

from .. import messages as host_msg
from ..components import ensure_feature_components
from .hook.execute import bind_hooked
from .hook.load import load_action_hook_templates, load_on_hook_fail, parse_user_config
from .ui_macros import register_ui_macro_shims


class FeatureBase:
    """Connect / ready / component check for one prefix extra instance."""

    def __init__(
        self,
        config,
        *,
        kind: str,
        option_keys=(),
        hook_actions=(),
        required_components=(),
        defer_commands: bool = False,
    ):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.kind = kind
        self.settings = None
        self._user = parse_user_config(config, option_keys)
        self._required_components = tuple(required_components)
        if hook_actions:
            self._hook_templates = load_action_hook_templates(
                config, self.printer, hook_actions
            )
            self._on_hook_fail = load_on_hook_fail(config)
            self._hooked = bind_hooked(
                self.printer, self._hook_templates, self._on_hook_fail, self.kind
            )
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        if not defer_commands:
            self._register_commands()

    def required_components(self):
        return self._required_components

    def _command_bindings(self):
        """``(name, handler, desc)`` tuples. Empty when the extra has no command."""
        return ()

    def ui_gcode_names(self):
        return [name for name, _handler, _desc in self._command_bindings()]

    def _register_commands(self, replace: bool = False) -> None:
        for name, handler, desc in self._command_bindings():
            if replace:
                self.gcode.register_command(name, None)
            self.gcode.register_command(name, handler, desc=desc)

    def _handle_connect(self):
        comps = ensure_feature_components(
            self.printer, self.kind, required=self.required_components()
        )
        self.on_components(comps)
        self.on_connect()

    def on_components(self, comps) -> None:
        """Called after host (and required extras) exist. Default no-op."""

    def on_connect(self) -> None:
        """Resolve, check fan object, validate, UI shims. Hook overrides to no-op."""
        try:
            self.settings = self.resolve_settings()
        except ValueError as e:
            raise self.printer.config_error(str(e)) from e
        self._ensure_fan_object()
        self._raise_validation(self.validate_settings())
        names = self.ui_gcode_names()
        if names:
            register_ui_macro_shims(self.printer, names)

    def resolve_settings(self):
        raise NotImplementedError("%s.resolve_settings" % (type(self).__name__,))

    def validate_settings(self):
        raise NotImplementedError("%s.validate_settings" % (type(self).__name__,))

    def _ensure_fan_object(self) -> None:
        s = self.settings
        fan = getattr(s, "fan", None)
        if s is None or fan is None:
            return
        if self.printer.lookup_object(fan, None) is None:
            raise self.printer.config_error(host_msg.fan_missing(fan))

    def _raise_validation(self, result) -> None:
        for issue in result.warnings:
            logging.warning("%s", issue.message)
        if result.errors:
            raise self.printer.config_error(
                host_msg.config_validation_failed([e.message for e in result.errors])
            )

    def _handle_ready(self):
        self.on_ready()

    def on_ready(self) -> None:
        """After ``klippy:ready``. Default no-op."""

    def status_core(self) -> dict:
        return {"kind": self.kind, "enabled": True}
