"""Klipper I/O runner for one wipe feature instance."""

from __future__ import annotations

import logging

from ... import messages as host_msg
from . import messages as msg
from .constants import (
    CMD_ABSOLUTE,
    CMD_RESTORE_GCODE_STATE,
    CMD_SAVE_GCODE_STATE,
    DEFAULT_FAN_OBJECT,
)
from .hints import collect_wipe_hints
from .resolve import plan_wipe_moves
from .types import WipeMove, WipePathSettings
from .validate import validate_path


def config_has(config, name):
    try:
        return config.fileconfig.has_option(config.get_name(), name)
    except Exception:
        return False


def parse_user_config(config, option_keys) -> dict:
    user = {}
    for key in option_keys:
        if config_has(config, key):
            user[key] = config.get(key)
    return user


class WipeRunner:
    """One prefix section. Settings are instance-local (no shared wipe state)."""

    def __init__(self, config, spec):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.spec = spec
        self.kind = spec.kind
        self.gcode_name = spec.gcode
        self._user = parse_user_config(config, spec.option_keys)
        self.settings = None
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.gcode.register_command(
            self.gcode_name,
            self.cmd_wipe,
            desc=spec.help_text,
        )

    def _handle_connect(self):
        host = self.printer.lookup_object("klipper_common", None)
        if host is None:
            raise self.printer.config_error(host_msg.feature_requires_host(self.kind))
        hints = collect_wipe_hints(self.printer)
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

    def cmd_wipe(self, gcmd):
        s = self.settings
        if s is None:
            raise gcmd.error(msg.not_ready())
        toolhead = self.printer.lookup_object("toolhead")
        eventtime = self.printer.get_reactor().monotonic()
        homed = toolhead.get_status(eventtime).get("homed_axes", "")
        if not all(axis in homed for axis in "xyz"):
            raise gcmd.error(msg.not_homed())
        have_temp = self._wait_nozzle(gcmd)
        prev_fan = self._fan_speed_now(eventtime) if have_temp else 0.0
        state_name = self.gcode_name
        self._save_gcode_state(state_name)
        try:
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
            if have_temp and s.retract > 0:
                self.gcode.run_script_from_command(
                    "G91\nG1 E%.3f F%.0f\nG90" % (-s.retract, s.retract_speed * 60.0)
                )
            if have_temp:
                self._set_fan(s.fan_speed)
            for move in plan_wipe_moves(s):
                self._emit_move(move)
        finally:
            if have_temp:
                self._restore_fan(prev_fan)
            self._restore_gcode_state(state_name, s)

    def _save_gcode_state(self, state_name: str) -> None:
        self.gcode.run_script_from_command(CMD_SAVE_GCODE_STATE % (state_name,))

    def _restore_gcode_state(self, state_name: str, settings: WipePathSettings) -> None:
        """Return XYZ and G-code mode to the snapshot. Fan is restored separately."""
        try:
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
            self.gcode.run_script_from_command(
                "G1 Z%.3f F%.0f" % (settings.z_hop, settings.travel_speed * 60.0)
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

    def _wait_nozzle(self, gcmd) -> bool:
        """Return True if nozzle temperature was verified, False if skipped (no temp info).

        When neither nozzle_temperature nor min_nozzle_temp is available, the check
        is skipped and all extruder operations (retract, fan) are also skipped.
        """
        s = self.settings
        if s.nozzle_temperature is None and s.min_nozzle_temp is None:
            gcmd.respond_info(msg.skip_nozzle_wait())
            logging.warning("%s", msg.skip_nozzle_wait())
            return False
        if s.nozzle_temperature is not None:
            self.gcode.run_script_from_command("M109 S%.1f" % (s.nozzle_temperature,))
            return True
        extruder = self.printer.lookup_object("extruder", None)
        if extruder is None:
            raise gcmd.error(msg.no_extruder())
        heater = extruder.get_heater()
        eventtime = self.printer.get_reactor().monotonic()
        current, target = heater.get_temp(eventtime)
        minimum = s.min_nozzle_temp
        if current >= minimum:
            return True
        if target >= minimum:
            self.gcode.run_script_from_command("M109 S%.1f" % (target,))
            return True
        raise gcmd.error(msg.nozzle_too_cold(current, minimum))

    def _fan_speed_now(self, eventtime) -> float:
        s = self.settings
        if s is None or s.fan is None:
            return 0.0
        fan = self.printer.lookup_object(s.fan, None)
        if fan is None:
            return 0.0
        try:
            return float(fan.get_status(eventtime).get("speed", 0.0) or 0.0)
        except Exception:
            return 0.0

    def _set_fan(self, speed: float) -> None:
        s = self.settings
        if s is None or s.fan is None:
            return
        self._apply_fan(s.fan, speed)

    def _restore_fan(self, speed: float) -> None:
        s = self.settings
        if s is None or s.fan is None:
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

    def _emit_move(self, move: WipeMove) -> None:
        parts = ["G1"]
        if move.x is not None:
            parts.append("X%.3f" % (move.x,))
        if move.y is not None:
            parts.append("Y%.3f" % (move.y,))
        if move.z is not None:
            parts.append("Z%.3f" % (move.z,))
        parts.append("F%.0f" % (move.speed * 60.0,))
        self.gcode.run_script_from_command(" ".join(parts))

    def get_status(self, eventtime):
        s = self.settings
        if s is None:
            return {"kind": self.kind, "enabled": True, "gcode": self.gcode_name}
        return {
            "kind": self.kind,
            "enabled": True,
            "gcode": self.gcode_name,
            "start_x": s.start_x,
            "start_y": s.start_y,
            "end_x": s.end_x,
            "end_y": s.end_y,
            "wipe_z": s.wipe_z,
            "z_hop": s.z_hop,
            "passes": s.passes,
        }
