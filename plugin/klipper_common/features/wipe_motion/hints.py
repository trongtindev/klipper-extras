"""Collect wipe hints from live Klipper objects."""

from __future__ import annotations

from .constants import DEFAULT_FAN_OBJECT
from .types import WipeKlipperHints


def _eventtime(printer) -> float:
    try:
        return float(printer.get_reactor().monotonic())
    except Exception:
        return 0.0


def _config_has(printer, section: str, option: str) -> bool:
    try:
        cf = printer.lookup_object("configfile", None)
        if cf is None:
            return False
        return bool(cf.fileconfig.has_option(section, option))
    except Exception:
        return False


def collect_wipe_hints(printer) -> WipeKlipperHints:
    """Read live Klipper objects. Missing objects stay None."""
    eventtime = _eventtime(printer)
    max_velocity = None
    toolhead = printer.lookup_object("toolhead", None)
    if toolhead is not None:
        try:
            max_velocity = float(toolhead.max_velocity)
        except Exception:
            max_velocity = None
        if max_velocity is None:
            try:
                st = toolhead.get_status(eventtime)
                max_velocity = float(st["max_velocity"])
            except Exception:
                max_velocity = None
    min_nozzle_temp = None
    extruder = printer.lookup_object("extruder", None)
    if extruder is not None and _config_has(printer, "extruder", "min_extrude_temp"):
        try:
            min_nozzle_temp = float(extruder.min_extrude_temp)
        except Exception:
            min_nozzle_temp = None
    retract = retract_speed = None
    fw = printer.lookup_object("firmware_retraction", None)
    if fw is not None:
        try:
            retract = float(fw.retract_length)
        except Exception:
            retract = None
        try:
            retract_speed = float(fw.retract_speed)
        except Exception:
            retract_speed = None
    z_hop = None
    safe_z = printer.lookup_object("safe_z_home", None)
    if safe_z is not None:
        try:
            hop = float(safe_z.z_hop)
            if hop > 0:
                z_hop = hop
        except Exception:
            z_hop = None
    fan = None
    if printer.lookup_object(DEFAULT_FAN_OBJECT, None) is not None:
        fan = DEFAULT_FAN_OBJECT
    return WipeKlipperHints(
        max_velocity=max_velocity,
        min_nozzle_temp=min_nozzle_temp,
        retract=retract,
        retract_speed=retract_speed,
        z_hop=z_hop,
        fan=fan,
    )
