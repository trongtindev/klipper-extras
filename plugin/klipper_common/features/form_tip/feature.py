"""Klipper extra instance for [klipper_common form_tip]."""

from __future__ import annotations

import logging

from ... import messages as host_msg
from . import messages as msg
from .constants import (
    CMD_ABSOLUTE,
    CMD_EXTRUDE_ABS,
    CMD_RESTORE_STATE_FORM_TIP,
    CMD_SAVE_STATE_FORM_TIP,
    GCODE,
    HELP_TEXT,
    KIND,
    OPTION_KEYS,
)
from .resolve import overlay_gcode_params, plan_tip_steps, resolve_tip_settings
from .types import FormTipHints
from .validate import validate_tip


def _config_has(config, name):
    try:
        return config.fileconfig.has_option(config.get_name(), name)
    except Exception:
        return False


def _parse_user_config(config) -> dict:
    user = {}
    for key in OPTION_KEYS:
        if _config_has(config, key):
            user[key] = config.get(key)
    return user


class FormTipRunner:
    """One [klipper_common form_tip] section. Settings are instance-local."""

    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.kind = KIND
        self.gcode_name = GCODE
        self._user = _parse_user_config(config)
        self.settings = None
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.gcode.register_command(
            self.gcode_name,
            self.cmd_FORM_TIP,
            desc=HELP_TEXT,
        )

    def _handle_connect(self):
        host = self.printer.lookup_object("klipper_common", None)
        if host is None:
            raise self.printer.config_error(
                host_msg.feature_requires_host(self.kind)
            )
        hints = self._collect_hints()
        try:
            self.settings = resolve_tip_settings(
                self.kind, self.gcode_name, self._user, hints
            )
        except ValueError as e:
            raise self.printer.config_error(str(e)) from e
        # Validate fan object at connect
        if self.settings.fan is not None:
            if self.printer.lookup_object(self.settings.fan, None) is None:
                raise self.printer.config_error(msg.fan_missing(self.settings.fan))
        result = validate_tip(self.settings)
        for issue in result.warnings:
            logging.warning("%s", issue.message)
        if result.errors:
            raise self.printer.config_error(
                host_msg.config_validation_failed(
                    [e.message for e in result.errors]
                )
            )

    def _collect_hints(self) -> FormTipHints:
        max_extrude_only_velocity = None
        extruder = self.printer.lookup_object("extruder", None)
        if extruder is not None:
            try:
                max_extrude_only_velocity = float(
                    extruder.max_extrude_only_velocity
                )
            except Exception:
                max_extrude_only_velocity = None
        min_nozzle_temp = None
        if extruder is not None and self._cfg_has("extruder", "min_extrude_temp"):
            try:
                min_nozzle_temp = float(extruder.min_extrude_temp)
            except Exception:
                min_nozzle_temp = None
        fan = None
        if self.printer.lookup_object("fan", None) is not None:
            fan = "fan"
        return FormTipHints(
            max_extrude_only_velocity=max_extrude_only_velocity,
            min_nozzle_temp=min_nozzle_temp,
            fan=fan,
        )

    def _cfg_has(self, section: str, option: str) -> bool:
        try:
            cf = self.printer.lookup_object("configfile", None)
            if cf is None:
                return False
            return bool(cf.fileconfig.has_option(section, option))
        except Exception:
            return False

    def cmd_FORM_TIP(self, gcmd):
        s = self.settings
        if s is None:
            raise gcmd.error(msg.not_ready())

        # Apply G-code param overrides
        try:
            s = overlay_gcode_params(gcmd, s)
        except ValueError as e:
            raise gcmd.error(str(e)) from e

        # Validate overlaid settings
        result = validate_tip(s)
        if result.errors:
            raise gcmd.error(
                host_msg.config_validation_failed(
                    [e.message for e in result.errors]
                )
            )

        # Fan speed before
        prev_fan = self._fan_speed_now()

        self._save_gcode_state()
        try:
            # Phase 0: Heat wait
            self._wait_nozzle(gcmd, s)

            # M83 (relative extrusion)
            self.gcode.run_script_from_command(CMD_EXTRUDE_ABS)

            # Emit all phases (fan_on is inside plan_tip_steps, before cooling)
            for step in plan_tip_steps(s):
                self.gcode.run_script_from_command(step.command)

        finally:
            self._restore_fan(prev_fan)
            self._restore_gcode_state()

    def _save_gcode_state(self) -> None:
        try:
            self.gcode.run_script_from_command(CMD_SAVE_STATE_FORM_TIP)
        except Exception:
            logging.warning(
                "klipper_common: save gcode state FORM_TIP failed",
                exc_info=True,
            )

    def _restore_gcode_state(self) -> None:
        try:
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
        except Exception:
            logging.debug("klipper_common: G90 before restore failed", exc_info=True)
        try:
            self.gcode.run_script_from_command(CMD_RESTORE_STATE_FORM_TIP)
        except Exception:
            logging.warning(
                "%s",
                msg.restore_gcode_state_failed(self.gcode_name),
                exc_info=True,
            )

    def _wait_nozzle(self, gcmd, s) -> None:
        if s.nozzle_temperature is None and s.min_nozzle_temp is None:
            gcmd.respond_info(msg.skip_nozzle_wait())
            logging.warning("%s", msg.skip_nozzle_wait())
            return
        extruder = self.printer.lookup_object("extruder", None)
        if extruder is None:
            raise gcmd.error(msg.no_extruder())
        heater = extruder.get_heater()
        eventtime = self.printer.get_reactor().monotonic()
        current, target = heater.get_temp(eventtime)
        if s.nozzle_temperature is not None:
            self.gcode.run_script_from_command(
                "M109 S%.1f" % (s.nozzle_temperature,)
            )
            return
        minimum = s.min_nozzle_temp
        if current >= minimum:
            return
        if target >= minimum:
            self.gcode.run_script_from_command("M109 S%.1f" % (target,))
            return
        raise gcmd.error(msg.nozzle_too_cold(current, minimum))

    def _fan_speed_now(self) -> float:
        s = self.settings
        if s is None or s.fan is None:
            return 0.0
        fan = self.printer.lookup_object(s.fan, None)
        if fan is None:
            return 0.0
        try:
            return float(fan.get_status(
                self.printer.get_reactor().monotonic()
            ).get("speed", 0.0) or 0.0)
        except Exception:
            return 0.0

    def _set_fan(self, fan_name: str, speed: float) -> None:
        if fan_name == "fan":
            self.gcode.run_script_from_command(
                "M106 S%.0f" % (speed * 255.0,)
            )
        else:
            self.gcode.run_script_from_command(
                "SET_FAN_SPEED FAN=%s SPEED=%.3f" % (fan_name, speed)
            )

    def _restore_fan(self, speed: float) -> None:
        s = self.settings
        if s is None or s.fan is None:
            return
        try:
            self._set_fan(s.fan, speed)
        except Exception:
            logging.debug("klipper_common: restore fan failed", exc_info=True)

    def get_status(self, eventtime):
        s = self.settings
        if s is None:
            return {"kind": self.kind, "enabled": True, "gcode": self.gcode_name}
        return {
            "kind": self.kind,
            "enabled": True,
            "gcode": self.gcode_name,
            "profile": s.profile_name,
            "tip_distance": s.tip_distance,
            "sep_fast_len": s.sep_fast_len,
            "sep_slow_len": s.sep_slow_len,
            "cooling_moves": s.cooling_moves,
            "use_skinnydip": s.use_skinnydip,
        }


def load_feature(config):
    return FormTipRunner(config)
