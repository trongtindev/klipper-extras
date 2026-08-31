"""Klipper I/O runner for one purge feature instance."""

from __future__ import annotations

import logging
from dataclasses import replace as dataclass_replace

from ... import messages as host_msg
from ..hook.execute import bind_hooked, call_common_hook
from ..hook.load import load_action_hook_templates, load_on_hook_fail, parse_user_config
from . import messages as msg
from .constants import (
    CMD_ABSOLUTE,
    CMD_EXTRUDE_REL,
    CMD_RESTORE_GCODE_STATE,
    CMD_SAVE_GCODE_STATE,
    DEFAULT_FAN_OBJECT,
    LEVELING_OBJECT_COMMANDS,
    ORIGIN_ADAPTIVE,
    PURGE_HOOK_ACTIONS,
)
from .hints import collect_object_aabb, collect_purge_hints
from .resolve import (
    heat_wait_target,
    overlay_purge_amount,
    plan_purge_actions,
    resolve_bed_origin,
)
from .types import PurgeMove, PurgePathSettings
from .validate import validate_path


def unset_leveling_commands(printer, eventtime):
    """G-code names of loaded QGL / Z_TILT_ADJUST extras that are not applied."""
    missing = []
    for obj_name, command in LEVELING_OBJECT_COMMANDS:
        obj = printer.lookup_object(obj_name, None)
        if obj is None:
            continue
        if not obj.get_status(eventtime).get("applied"):
            missing.append(command)
    return missing


class PurgeRunner:
    """One prefix section. Settings are instance-local (no shared purge state)."""

    def __init__(self, config, spec):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.spec = spec
        self.kind = spec.kind
        self.gcode_name = spec.gcode
        self._user = parse_user_config(config, spec.option_keys)
        self.settings = None
        self._hook_templates = load_action_hook_templates(
            config, self.printer, PURGE_HOOK_ACTIONS
        )
        self._on_hook_fail = load_on_hook_fail(config)
        self._hooked = bind_hooked(
            self.printer, self._hook_templates, self._on_hook_fail, self.kind
        )
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.gcode.register_command(
            self.gcode_name,
            self.cmd_purge,
            desc=spec.help_text,
        )

    def _handle_connect(self):
        host = self.printer.lookup_object("klipper_common", None)
        if host is None:
            raise self.printer.config_error(host_msg.feature_requires_host(self.kind))
        hints = collect_purge_hints(self.printer)
        try:
            self.settings = self.spec.resolve(self._user, hints)
        except ValueError as e:
            raise self.printer.config_error(str(e)) from e
        if self.settings.fan is not None:
            if self.printer.lookup_object(self.settings.fan, None) is None:
                raise self.printer.config_error(msg.fan_missing(self.settings.fan))
        result = validate_path(self.settings)
        for issue in result.warnings:
            logging.warning("%s", issue.message)
        if result.errors:
            raise self.printer.config_error(
                host_msg.config_validation_failed([e.message for e in result.errors])
            )

    def cmd_purge(self, gcmd):
        base = self.settings
        if base is None:
            raise gcmd.error(msg.not_ready())
        toolhead = self.printer.lookup_object("toolhead")
        eventtime = self.printer.get_reactor().monotonic()
        homed = toolhead.get_status(eventtime).get("homed_axes", "")
        if not all(axis in homed for axis in "xyz"):
            raise gcmd.error(msg.not_homed())
        for command in unset_leveling_commands(self.printer, eventtime):
            text = msg.leveling_not_applied(command)
            gcmd.respond_info(text)
            logging.warning("%s", text)
        try:
            amount = gcmd.get_float("PURGE_AMOUNT", None)
            if amount is None:
                amount = gcmd.get_float("PURGE_LENGTH", None)
            s = overlay_purge_amount(base, amount)
        except ValueError as e:
            raise gcmd.error(str(e)) from e
        if s.origin_mode == ORIGIN_ADAPTIVE:
            aabb = collect_object_aabb(self.printer)
            try:
                ox, oy = resolve_bed_origin(s, aabb)
            except ValueError as e:
                raise gcmd.error(str(e)) from e
            s = dataclass_replace(s, start_x=ox, start_y=oy)
        result = validate_path(s)
        if result.errors:
            raise gcmd.error(
                host_msg.config_validation_failed([e.message for e in result.errors])
            )
        try:
            steps = plan_purge_actions(s)
        except ValueError as e:
            raise gcmd.error(str(e)) from e
        prev_fan = self._fan_speed_now(eventtime, s)
        state_name = self.gcode_name
        self._save_gcode_state(state_name)
        have_temp = False
        try:
            extra_kind = {"kind": self.kind}
            call_common_hook(self.printer, "before", extra_kind)
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
            self.gcode.run_script_from_command(CMD_EXTRUDE_REL)
            have_temp = self._hooked("heat", lambda: self._wait_nozzle(gcmd, s))
            if have_temp and s.fan is not None:
                self._hooked("fan", lambda: self._set_fan(s, s.fan_speed))
            for step in steps:
                extra = {}
                if step.pass_index is not None:
                    extra["pass_index"] = step.pass_index
                self._hooked(
                    step.name,
                    lambda moves=step.moves: self._emit_moves(moves),
                    extra,
                )
            call_common_hook(self.printer, "after", extra_kind)
        finally:
            if have_temp:
                self._restore_fan(s, prev_fan)
            self._restore_gcode_state(state_name, s)

    def _emit_moves(self, moves) -> None:
        for move in moves:
            self._emit_move(move)

    def _save_gcode_state(self, state_name: str) -> None:
        self.gcode.run_script_from_command(CMD_SAVE_GCODE_STATE % (state_name,))

    def _restore_gcode_state(self, state_name: str, settings: PurgePathSettings) -> None:
        try:
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
            self.gcode.run_script_from_command(
                "G1 Z%.3f F%.0f" % (settings.travel_z, settings.travel_speed * 60.0)
            )
        except Exception:
            logging.warning("%s", msg.lift_before_restore_failed(), exc_info=True)
        try:
            self.gcode.run_script_from_command(
                CMD_RESTORE_GCODE_STATE % (state_name, settings.travel_speed)
            )
        except Exception:
            logging.warning(
                "%s",
                msg.restore_gcode_state_failed(state_name),
                exc_info=True,
            )

    def _wait_nozzle(self, gcmd, s: PurgePathSettings) -> bool:
        if s.nozzle_temperature is None and s.min_nozzle_temp is None:
            raise gcmd.error(msg.heat_temp_required(s.kind))
        if s.nozzle_temperature is not None:
            wait = s.nozzle_temperature
        else:
            extruder = self.printer.lookup_object("extruder", None)
            if extruder is None:
                raise gcmd.error(msg.no_extruder())
            heater = extruder.get_heater()
            eventtime = self.printer.get_reactor().monotonic()
            current, target = heater.get_temp(eventtime)
            wait = heat_wait_target(None, s.min_nozzle_temp, current, target)
        if wait is not None:
            self.gcode.run_script_from_command("M109 S%.1f" % (wait,))
        return True

    def _fan_speed_now(self, eventtime, s: PurgePathSettings) -> float:
        if s.fan is None:
            return 0.0
        fan = self.printer.lookup_object(s.fan, None)
        if fan is None:
            return 0.0
        try:
            return float(fan.get_status(eventtime).get("speed", 0.0) or 0.0)
        except Exception:
            return 0.0

    def _set_fan(self, s: PurgePathSettings, speed: float) -> None:
        if s.fan is None:
            return
        self._apply_fan(s.fan, speed)

    def _restore_fan(self, s: PurgePathSettings, speed: float) -> None:
        if s.fan is None:
            return
        try:
            self._apply_fan(s.fan, speed)
        except Exception:
            logging.warning("%s", msg.restore_fan_failed(), exc_info=True)

    def _apply_fan(self, fan_name: str, speed: float) -> None:
        if fan_name == DEFAULT_FAN_OBJECT:
            self.gcode.run_script_from_command("M106 S%.0f" % (speed * 255.0,))
            return
        self.gcode.run_script_from_command(
            "SET_FAN_SPEED FAN=%s SPEED=%.3f" % (fan_name, speed)
        )

    def _emit_move(self, move: PurgeMove) -> None:
        parts = ["G1"]
        if move.x is not None:
            parts.append("X%.3f" % (move.x,))
        if move.y is not None:
            parts.append("Y%.3f" % (move.y,))
        if move.z is not None:
            parts.append("Z%.3f" % (move.z,))
        if move.e is not None:
            parts.append("E%.4f" % (move.e,))
        parts.append("F%.0f" % (move.speed * 60.0,))
        self.gcode.run_script_from_command(" ".join(parts))

    def get_status(self, eventtime):
        s = self.settings
        if s is None:
            return {"kind": self.kind, "enabled": True, "gcode": self.gcode_name}
        status = {
            "kind": self.kind,
            "enabled": True,
            "gcode": self.gcode_name,
            "origin_mode": s.origin_mode,
            "start_x": s.start_x,
            "start_y": s.start_y,
            "purge_z": s.purge_z,
            "purge_amount": s.purge_amount,
        }
        if s.style is not None:
            status["style"] = s.style
        return status
