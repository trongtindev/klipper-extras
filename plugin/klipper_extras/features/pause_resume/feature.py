"""Klipper extra instance for [klipper_extras pause_resume]."""

from __future__ import annotations

import logging

from ... import klipper_fields as kf, messages as host_msg
from ...components import ensure_feature_components
from ...respond_action import prompt_end, prompt_show, respond_error
from ..gcode import gcode_f
from ..hook.execute import bind_hooked, call_common_hook
from ..hook.load import load_action_hook_templates, load_on_hook_fail, parse_user_config
from ..ui_macros import register_ui_macro_shims
from . import messages as msg
from .constants import (
    GCODES,
    HELP_CANCEL,
    HELP_PAUSE,
    HELP_RESUME,
    KIND,
    OPTION_KEYS,
    PAUSE_RESUME_HOOK_ACTIONS,
    PRINT_STATE_PAUSED,
    PRINT_STATE_PRINTING,
    REQUIRED_COMPONENTS,
)
from .resolve import overlay_pause_xy, resolve_pause_settings
from .types import PauseResumeHints, PauseResumeSettings
from .validate import validate_pause


class PauseResumeRunner:
    """Owns PAUSE, RESUME, CANCEL_PRINT. Settings are instance-local."""

    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.kind = KIND
        self._user = parse_user_config(config, OPTION_KEYS)
        self.settings = None
        self._base = None
        self._hook_templates = load_action_hook_templates(
            config, self.printer, PAUSE_RESUME_HOOK_ACTIONS
        )
        self._on_hook_fail = load_on_hook_fail(config)
        self._hooked = bind_hooked(
            self.printer, self._hook_templates, self._on_hook_fail, self.kind
        )
        self._saved_extruder_target = 0.0
        self._saved_idle_timeout = 0.0
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_connect(self):
        extra_required = []
        sensor = self._user.get("runout_sensor")
        if sensor is not None and str(sensor).strip():
            extra_required.append(str(sensor).strip())
        idle_raw = self._user.get("idle_timeout")
        if idle_raw is not None and str(idle_raw).strip():
            extra_required.append("idle_timeout")
        comps = ensure_feature_components(
            self.printer,
            self.kind,
            required=REQUIRED_COMPONENTS + tuple(extra_required),
        )
        self._base = comps["pause_resume"]
        hints = PauseResumeHints(
            max_velocity=kf.max_velocity(self.printer),
            z_hop=kf.safe_z_hop(self.printer),
            retract=kf.firmware_retract(self.printer)[0],
            retract_speed=kf.firmware_retract(self.printer)[1],
        )
        try:
            self.settings = resolve_pause_settings(self._user, hints)
        except ValueError as e:
            raise self.printer.config_error(str(e)) from e
        result = validate_pause(self.settings)
        for issue in result.warnings:
            logging.warning("%s", issue.message)
        if result.errors:
            raise self.printer.config_error(
                host_msg.config_validation_failed([e.message for e in result.errors])
            )
        register_ui_macro_shims(self.printer, GCODES)

    def _handle_ready(self):
        """After gcode_macro rename_existing (connect). Owns PAUSE/RESUME/CANCEL_PRINT."""
        if self.settings is None or self._base is None:
            return
        self._steal_commands()

    def _steal_commands(self) -> None:
        pairs = (
            ("PAUSE", self.cmd_PAUSE, HELP_PAUSE),
            ("RESUME", self.cmd_RESUME, HELP_RESUME),
            ("CANCEL_PRINT", self.cmd_CANCEL_PRINT, HELP_CANCEL),
        )
        for name, handler, desc in pairs:
            self.gcode.register_command(name, None)
            self.gcode.register_command(name, handler, desc=desc)

    def _extra(self, command: str) -> dict:
        return {"kind": self.kind, "command": command}

    def _is_paused(self) -> bool:
        return bool(self._base is not None and self._base.is_paused)

    def _print_state(self) -> str:
        ps = self.printer.lookup_object("print_stats", None)
        if ps is None:
            return ""
        try:
            eventtime = self.printer.get_reactor().monotonic()
            return str(ps.get_status(eventtime).get("state") or "")
        except (AttributeError, TypeError, ValueError):
            return ""

    def _can_extrude(self) -> bool:
        extruder = self.printer.lookup_object("extruder", None)
        if extruder is None:
            return False
        try:
            return bool(extruder.get_heater().can_extrude)
        except (AttributeError, TypeError):
            return False

    def _extruder_target(self) -> float:
        extruder = self.printer.lookup_object("extruder", None)
        if extruder is None:
            return 0.0
        try:
            heater = extruder.get_heater()
            eventtime = self.printer.get_reactor().monotonic()
            _cur, target = heater.get_temp(eventtime)
            return float(target)
        except (AttributeError, TypeError, ValueError):
            return 0.0

    def _homed(self) -> str:
        toolhead = self.printer.lookup_object("toolhead", None)
        if toolhead is None:
            return ""
        try:
            eventtime = self.printer.get_reactor().monotonic()
            return str(toolhead.get_status(eventtime).get("homed_axes", "") or "")
        except (AttributeError, TypeError, ValueError):
            return ""

    def _position_z(self):
        toolhead = self.printer.lookup_object("toolhead", None)
        if toolhead is None:
            return None
        try:
            pos = toolhead.get_position()
            return float(pos[2])
        except (AttributeError, TypeError, ValueError, IndexError):
            return None

    def _axis_max_z(self):
        toolhead = self.printer.lookup_object("toolhead", None)
        if toolhead is None:
            return None
        try:
            eventtime = self.printer.get_reactor().monotonic()
            box = toolhead.get_status(eventtime).get("axis_maximum")
            return float(box.z)
        except (AttributeError, TypeError, ValueError):
            return None

    def _apply_idle_timeout(self, s: PauseResumeSettings) -> None:
        if s.idle_timeout <= 0:
            return
        idle = self.printer.lookup_object("idle_timeout", None)
        if idle is None:
            return
        try:
            eventtime = self.printer.get_reactor().monotonic()
            self._saved_idle_timeout = float(
                idle.get_status(eventtime).get("idle_timeout", 0.0) or 0.0
            )
        except (AttributeError, TypeError, ValueError):
            self._saved_idle_timeout = 0.0
        self.gcode.run_script_from_command(
            "SET_IDLE_TIMEOUT TIMEOUT=%.3f" % (s.idle_timeout,)
        )

    def _restore_idle_timeout(self) -> None:
        if self._saved_idle_timeout <= 0:
            return
        self.gcode.run_script_from_command(
            "SET_IDLE_TIMEOUT TIMEOUT=%.3f" % (self._saved_idle_timeout,)
        )
        self._saved_idle_timeout = 0.0

    def _filament_ok(self, s: PauseResumeSettings) -> bool:
        if not s.runout_sensor:
            return True
        sensor = self.printer.lookup_object(s.runout_sensor, None)
        if sensor is None:
            return True
        try:
            eventtime = self.printer.get_reactor().monotonic()
            st = sensor.get_status(eventtime)
        except (AttributeError, TypeError, ValueError):
            return True
        if not st.get("enabled", True):
            return True
        return bool(st.get("filament_detected", True))

    def _abort_resume(self, text: str) -> None:
        respond_error(self.gcode, text)
        prompt_show(
            self.gcode,
            msg.resume_aborted_title(),
            [text],
            [(msg.prompt_ok(), "RESPOND TYPE=command MSG=action:prompt_end", "")],
        )

    def _pause_settings(self, gcmd, s: PauseResumeSettings) -> PauseResumeSettings:
        x = gcmd.get_float("X", None)
        y = gcmd.get_float("Y", None)
        if (x is None) != (y is None):
            raise gcmd.error(msg.park_pair_required("X", "Y"))
        if x is not None:
            return overlay_pause_xy(s, x, y)
        return s

    def _do_retract(self, length: float, speed: float) -> None:
        self.gcode.run_script_from_command(
            "M83\nG1 E%.3f %s" % (-abs(length), gcode_f(speed))
        )

    def _do_unretract(self, length: float, speed: float) -> None:
        self.gcode.run_script_from_command(
            "M83\nG1 E%.3f %s" % (abs(length), gcode_f(speed))
        )

    def _do_z_hop(self, gcmd, s: PauseResumeSettings, z_min: float) -> None:
        homed = self._homed()
        if "z" not in homed:
            gcmd.respond_info(msg.not_homed_skip("z_hop"))
            return
        current_z = self._position_z()
        if current_z is None:
            gcmd.respond_info(msg.not_homed_skip("z_hop"))
            return
        z_park = max(current_z + s.z_hop, z_min)
        axis_max = self._axis_max_z()
        if axis_max is not None and z_park > axis_max:
            raise gcmd.error(msg.z_park_too_high(z_park, axis_max))
        self.gcode.run_script_from_command(
            "G90\nG1 Z%.3f %s" % (z_park, gcode_f(s.z_speed))
        )

    def _do_park(self, gcmd, park_x, park_y, s: PauseResumeSettings) -> None:
        homed = self._homed()
        if "x" not in homed or "y" not in homed:
            gcmd.respond_info(msg.not_homed_skip("park"))
            return
        self.gcode.run_script_from_command(
            "G90\nG1 X%.3f Y%.3f %s"
            % (park_x, park_y, gcode_f(s.travel_speed))
        )

    def _pause_actions(self, gcmd, s: PauseResumeSettings, z_min: float) -> None:
        if s.retract > 0:
            if self._can_extrude():
                self._do_retract(s.retract, s.retract_speed)
            else:
                gcmd.respond_info(msg.retract_skipped_cold())
                logging.warning("%s", msg.retract_skipped_cold())
        if s.z_hop != 0:
            self._do_z_hop(gcmd, s, z_min)
        if s.park_x is not None and s.park_y is not None:
            self._do_park(gcmd, s.park_x, s.park_y, s)

    def _resume_actions(self, gcmd, s: PauseResumeSettings) -> None:
        if not self._can_extrude():
            if s.restore_temperature and self._saved_extruder_target > 0:
                target = self._saved_extruder_target
                self.gcode.run_script_from_command("M109 S%.1f" % (target,))
            if not self._can_extrude():
                text = msg.resume_cold_text()
                self._abort_resume(text)
                raise gcmd.error(text)
        prompt_end(self.gcode)
        if s.unretract > 0 and self._can_extrude():
            self._do_unretract(s.unretract, s.unretract_speed)

    def _cancel_actions(self, gcmd, s: PauseResumeSettings) -> None:
        park_x = s.cancel_park_x if s.cancel_park_x is not None else s.park_x
        park_y = s.cancel_park_y if s.cancel_park_y is not None else s.park_y
        if s.park_at_cancel and park_x is not None and park_y is not None:
            if s.z_hop != 0:
                self._do_z_hop(gcmd, s, 0.0)
            self._do_park(gcmd, park_x, park_y, s)
        if s.cancel_retract > 0:
            if self._can_extrude():
                self._do_retract(s.cancel_retract, s.retract_speed)
            else:
                gcmd.respond_info(msg.retract_skipped_cold())
        self.gcode.run_script_from_command("TURN_OFF_HEATERS")
        self.gcode.run_script_from_command("M106 S0")

    def cmd_PAUSE(self, gcmd):
        s = self.settings
        if s is None or self._base is None:
            raise gcmd.error(msg.not_ready())
        if self._is_paused():
            gcmd.respond_info(msg.already_paused())
            return
        if self._print_state() != PRINT_STATE_PRINTING:
            gcmd.respond_info(msg.not_printing())
            return
        try:
            s = self._pause_settings(gcmd, s)
        except ValueError as e:
            raise gcmd.error(str(e)) from e
        z_min = gcmd.get_float("Z_MIN", 0.0)
        self._saved_extruder_target = self._extruder_target()
        self._apply_idle_timeout(s)
        self._base.cmd_PAUSE(gcmd)
        extra = self._extra("PAUSE")
        call_common_hook(self.printer, "before", extra)
        self._hooked("pause", lambda: self._pause_actions(gcmd, s, z_min))
        call_common_hook(self.printer, "after", extra)

    def cmd_RESUME(self, gcmd):
        s = self.settings
        if s is None or self._base is None:
            raise gcmd.error(msg.not_ready())
        if not self._is_paused():
            gcmd.respond_info(msg.not_paused())
            return
        sensor = s.runout_sensor
        if sensor is not None and not self._filament_ok(s):
            self._abort_resume(msg.resume_runout_text(sensor))
            return
        extra = self._extra("RESUME")
        call_common_hook(self.printer, "before", extra)
        self._hooked("resume", lambda: self._resume_actions(gcmd, s))
        call_common_hook(self.printer, "after", extra)
        self._restore_idle_timeout()
        self._base.cmd_RESUME(gcmd)

    def cmd_CANCEL_PRINT(self, gcmd):
        s = self.settings
        if s is None or self._base is None:
            raise gcmd.error(msg.not_ready())
        if not self._is_paused() and self._print_state() not in (
            PRINT_STATE_PRINTING,
            PRINT_STATE_PAUSED,
        ):
            gcmd.respond_info(msg.not_cancelling())
            return
        prompt_end(self.gcode)
        self._restore_idle_timeout()
        extra = self._extra("CANCEL_PRINT")
        call_common_hook(self.printer, "before", extra)
        self._hooked("cancel", lambda: self._cancel_actions(gcmd, s))
        call_common_hook(self.printer, "after", extra)
        self._base.cmd_CANCEL_PRINT(gcmd)

    def get_status(self, eventtime):
        s = self.settings
        paused = False
        if self._base is not None:
            try:
                paused = bool(self._base.get_status(eventtime).get("is_paused"))
            except (AttributeError, TypeError):
                paused = bool(getattr(self._base, "is_paused", False))
        return {
            "kind": self.kind,
            "gcodes": list(GCODES),
            "is_paused": paused,
            "park_x": None if s is None else s.park_x,
            "park_y": None if s is None else s.park_y,
            "z_hop": None if s is None else s.z_hop,
        }


def load_feature(config):
    return PauseResumeRunner(config)
