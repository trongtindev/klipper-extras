"""Read live Klipper objects for hints. Attribute names follow klippy source.

``lookup_object("configfile")`` is ``PrinterConfig`` (klippy/configfile.py):
file keys are ``status_raw_config``. ``fileconfig`` belongs to ``ConfigWrapper``
(the object passed to ``load_config``), not to PrinterConfig.
"""

from __future__ import annotations

import math
from typing import Optional


def eventtime(printer) -> float:
    try:
        return float(printer.get_reactor().monotonic())
    except (AttributeError, TypeError, ValueError):
        return 0.0


def config_has(printer, section: str, option: str) -> bool:
    """True when that key is in the loaded printer.cfg (not a getfloat default)."""
    cf = printer.lookup_object("configfile", None)
    if cf is None:
        return False
    raw = getattr(cf, "status_raw_config", None)
    if not isinstance(raw, dict):
        return False
    sec = raw.get(section)
    if not isinstance(sec, dict):
        return False
    return option in sec


def _float_attr(obj, name: str) -> Optional[float]:
    if obj is None:
        return None
    try:
        return float(getattr(obj, name))
    except (AttributeError, TypeError, ValueError):
        return None


def max_velocity(printer) -> Optional[float]:
    """``[printer] max_velocity`` via ``ToolHead.get_max_velocity()`` (toolhead.py)."""
    toolhead = printer.lookup_object("toolhead", None)
    if toolhead is None:
        return None
    try:
        vel, _accel = toolhead.get_max_velocity()
        return float(vel)
    except (AttributeError, TypeError, ValueError):
        return None


def min_extrude_temp(printer) -> Optional[float]:
    """``[extruder] min_extrude_temp`` only if that key is in the file.

    Stored on the heater (heaters.py) as ``Heater.min_extrude_temp``.
    ``PrinterExtruder.get_heater()`` (extruder.py). Klipper default 170 if
    omitted is not used.
    """
    if not config_has(printer, "extruder", "min_extrude_temp"):
        return None
    extruder = printer.lookup_object("extruder", None)
    if extruder is None:
        return None
    try:
        heater = extruder.get_heater()
        return float(heater.min_extrude_temp)
    except (AttributeError, TypeError, ValueError):
        return None


def filament_diameter(printer) -> Optional[float]:
    """Diameter from ``PrinterExtruder.filament_area`` (extruder.py).

    Config ``filament_diameter`` is not stored on the object.
    """
    extruder = printer.lookup_object("extruder", None)
    area = _float_attr(extruder, "filament_area")
    if area is None or area <= 0:
        return None
    return 2.0 * math.sqrt(area / math.pi)


def max_extrude_cross_section(printer) -> Optional[float]:
    """Live ``max_extrude_ratio * filament_area`` (extruder.py)."""
    extruder = printer.lookup_object("extruder", None)
    ratio = _float_attr(extruder, "max_extrude_ratio")
    area = _float_attr(extruder, "filament_area")
    if ratio is None or area is None:
        return None
    return ratio * area


def max_extrude_only_velocity(printer) -> Optional[float]:
    """``[extruder] max_extrude_only_velocity`` — ``max_e_velocity``."""
    extruder = printer.lookup_object("extruder", None)
    return _float_attr(extruder, "max_e_velocity")


def firmware_retract(printer):
    """``[firmware_retraction] retract_length`` / ``retract_speed``."""
    fw = printer.lookup_object("firmware_retraction", None)
    return (_float_attr(fw, "retract_length"), _float_attr(fw, "retract_speed"))


def safe_z_hop(printer) -> Optional[float]:
    """``[safe_z_home] z_hop`` when > 0 (Klipper default is 0 = no hop)."""
    safe_z = printer.lookup_object("safe_z_home", None)
    hop = _float_attr(safe_z, "z_hop")
    if hop is not None and hop > 0:
        return hop
    return None


def default_fan(printer) -> Optional[str]:
    """``[fan]`` extra object name if loaded (extras/fan.py ``load_config``)."""
    if printer.lookup_object("fan", None) is not None:
        return "fan"
    return None


def axis_xy_limits(printer):
    """Kinematics ``axis_minimum`` / ``axis_maximum`` (gcode.Coord ``x``/``y``)."""
    toolhead = printer.lookup_object("toolhead", None)
    if toolhead is None:
        return (None, None, None, None)
    try:
        st = toolhead.get_status(eventtime(printer))
    except (AttributeError, TypeError, ValueError):
        return (None, None, None, None)
    return (
        _coord_axis(st, "axis_minimum", "x"),
        _coord_axis(st, "axis_minimum", "y"),
        _coord_axis(st, "axis_maximum", "x"),
        _coord_axis(st, "axis_maximum", "y"),
    )


def _coord_axis(status: dict, key: str, axis: str):
    try:
        box = status.get(key)
        return float(getattr(box, axis))
    except (AttributeError, TypeError, ValueError):
        return None
