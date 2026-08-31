"""Collect purge hints from live Klipper objects."""

from __future__ import annotations

from .constants import DEFAULT_FAN_OBJECT
from .types import PurgeKlipperHints


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


def _axis_limit(status: dict, key: str, axis: str):
    try:
        box = status.get(key)
        if box is None:
            return None
        if hasattr(box, axis):
            return float(getattr(box, axis))
        return float(box[axis])
    except Exception:
        return None


def host_min_nozzle_temp_from_host(host):
    """Host floor without waiting for host ``klippy:connect`` (section order)."""
    if host is None:
        return None
    settings = getattr(host, "settings", None)
    if settings is not None:
        val = getattr(settings, "min_nozzle_temp", None)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                return None
    user = getattr(host, "_user", None) or {}
    raw = user.get("min_nozzle_temp")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def collect_purge_hints(printer) -> PurgeKlipperHints:
    """Read live Klipper objects. Missing objects stay None."""
    eventtime = _eventtime(printer)
    max_velocity = None
    axis_minimum_x = axis_minimum_y = None
    axis_maximum_x = axis_maximum_y = None
    toolhead = printer.lookup_object("toolhead", None)
    if toolhead is not None:
        try:
            max_velocity = float(toolhead.max_velocity)
        except Exception:
            max_velocity = None
        st = None
        try:
            st = toolhead.get_status(eventtime)
        except Exception:
            st = None
        if max_velocity is None and st is not None:
            try:
                max_velocity = float(st["max_velocity"])
            except Exception:
                max_velocity = None
        if st is not None:
            axis_minimum_x = _axis_limit(st, "axis_minimum", "x")
            axis_minimum_y = _axis_limit(st, "axis_minimum", "y")
            axis_maximum_x = _axis_limit(st, "axis_maximum", "x")
            axis_maximum_y = _axis_limit(st, "axis_maximum", "y")
    min_nozzle_temp = None
    filament_diameter = None
    max_extrude_cross_section = None
    max_extrude_only_velocity = None
    extruder = printer.lookup_object("extruder", None)
    if extruder is not None:
        if _config_has(printer, "extruder", "min_extrude_temp"):
            try:
                min_nozzle_temp = float(extruder.min_extrude_temp)
            except Exception:
                min_nozzle_temp = None
        try:
            filament_diameter = float(extruder.filament_diameter)
        except Exception:
            filament_diameter = None
        try:
            max_extrude_cross_section = float(extruder.max_extrude_cross_section)
        except Exception:
            max_extrude_cross_section = None
        try:
            max_extrude_only_velocity = float(extruder.max_extrude_only_velocity)
        except Exception:
            max_extrude_only_velocity = None
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
    host_min_nozzle_temp = host_min_nozzle_temp_from_host(
        printer.lookup_object("klipper_common", None)
    )
    return PurgeKlipperHints(
        max_velocity=max_velocity,
        min_nozzle_temp=min_nozzle_temp,
        host_min_nozzle_temp=host_min_nozzle_temp,
        retract=retract,
        retract_speed=retract_speed,
        z_hop=z_hop,
        fan=fan,
        filament_diameter=filament_diameter,
        max_extrude_cross_section=max_extrude_cross_section,
        max_extrude_only_velocity=max_extrude_only_velocity,
        axis_minimum_x=axis_minimum_x,
        axis_minimum_y=axis_minimum_y,
        axis_maximum_x=axis_maximum_x,
        axis_maximum_y=axis_maximum_y,
    )


def collect_object_aabb(printer):
    """Return (x_min, y_min, x_max, y_max) from exclude_object, or None."""
    eo = printer.lookup_object("exclude_object", None)
    if eo is None:
        return None
    try:
        eventtime = _eventtime(printer)
        st = eo.get_status(eventtime)
        objects = st.get("objects") or []
    except Exception:
        return None
    xs = []
    ys = []
    for obj in objects:
        try:
            polygon = obj.get("polygon") or []
        except Exception:
            continue
        for point in polygon:
            try:
                xs.append(float(point[0]))
                ys.append(float(point[1]))
            except Exception:
                continue
    if not xs or not ys:
        return None
    return (min(xs), min(ys), max(xs), max(ys))
