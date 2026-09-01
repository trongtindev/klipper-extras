"""Klipper extra instance for [klipper_extras form_tip]."""

from __future__ import annotations

import logging

from ... import klipper_fields as kf, messages as host_msg
from ...constants import heat_floor_from_min_extrude_temp
from ..base import FeatureBase
from ..gcode_state import parse_restore_move
from ..hook.execute import call_common_hook
from . import messages as msg
from .constants import (
    CMD_ABSOLUTE,
    CMD_EXTRUDE_ABS,
    CMD_RESTORE_STATE_FORM_TIP,
    CMD_SAVE_STATE_FORM_TIP,
    FORM_TIP_HOOK_ACTIONS,
    GCODE,
    HELP_TEXT,
    KIND,
    OPTION_KEYS,
)
from .resolve import overlay_gcode_params, plan_tip_steps, resolve_tip_settings
from .types import FormTipHints
from .validate import validate_tip


def _tip_step_hook(label: str):
    """Map a planned step label to (action name, extra context)."""
    if label.startswith("cool_"):
        return "cool", {"pass_index": int(label.split("_", 1)[1])}
    if label == "fan_on":
        return "fan", None
    return label, None


class FormTipRunner(FeatureBase):
    """One [klipper_extras form_tip] section. Settings are instance-local."""

    def __init__(self, config):
        self.gcode_name = GCODE
        super().__init__(
            config,
            kind=KIND,
            option_keys=OPTION_KEYS,
            hook_actions=FORM_TIP_HOOK_ACTIONS,
        )

    def _command_bindings(self):
        return ((self.gcode_name, self.cmd_FORM_TIP, HELP_TEXT),)

    def resolve_settings(self):
        return resolve_tip_settings(
            self.kind, self.gcode_name, self._user, self._collect_hints()
        )

    def validate_settings(self):
        return validate_tip(self.settings)

    def _collect_hints(self) -> FormTipHints:
        return FormTipHints(
            max_extrude_only_velocity=kf.max_extrude_only_velocity(self.printer),
            min_nozzle_temp=heat_floor_from_min_extrude_temp(
                kf.min_extrude_temp(self.printer)
            ),
            fan=kf.default_fan(self.printer),
        )

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

        will_heat = not (
            s.nozzle_temperature is None and s.min_nozzle_temp is None
        )
        move = parse_restore_move(gcmd)
        self._save_gcode_state()
        try:
            extra_kind = {"kind": self.kind}
            call_common_hook(self.printer, "before", extra_kind)
            if will_heat:
                self._hooked("heat", lambda: self._wait_nozzle(gcmd, s))
            else:
                self._wait_nozzle(gcmd, s)

            self.gcode.run_script_from_command(CMD_EXTRUDE_ABS)

            for step in plan_tip_steps(s):
                action, extra = _tip_step_hook(step.label)
                self._hooked(
                    action,
                    lambda cmd=step.command: self.gcode.run_script_from_command(cmd),
                    extra,
                )

            call_common_hook(self.printer, "after", extra_kind)
        finally:
            self._restore_fan(prev_fan)
            self._restore_gcode_state(move)

    def _save_gcode_state(self) -> None:
        try:
            self.gcode.run_script_from_command(CMD_SAVE_STATE_FORM_TIP)
        except Exception:
            logging.warning(
                "%s", host_msg.line("save gcode state FORM_TIP failed"), exc_info=True
            )

    def _restore_gcode_state(self, move: int = 0) -> None:
        try:
            self.gcode.run_script_from_command(CMD_ABSOLUTE)
        except Exception:
            logging.warning(
                "%s", host_msg.line("G90 before restore failed"), exc_info=True
            )
        speed = kf.max_velocity(self.printer)
        if speed is None:
            logging.warning(
                "%s", host_msg.line("RESTORE MOVE_SPEED missing max_velocity")
            )
            script = "RESTORE_GCODE_STATE NAME=FORM_TIP MOVE=%d" % (move,)
        else:
            script = CMD_RESTORE_STATE_FORM_TIP % (move, speed)
        try:
            self.gcode.run_script_from_command(script)
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
            logging.debug("%s", msg.restore_fan_failed(), exc_info=True)

    def get_status(self, eventtime):
        status = self.status_core()
        status["gcode"] = self.gcode_name
        s = self.settings
        if s is None:
            return status
        status.update(
            {
                "profile": s.profile_name,
                "tip_distance": s.tip_distance,
                "sep_fast_len": s.sep_fast_len,
                "sep_slow_len": s.sep_slow_len,
                "cooling_moves": s.cooling_moves,
                "use_skinnydip": s.use_skinnydip,
            }
        )
        return status


def load_feature(config):
    return FormTipRunner(config)
