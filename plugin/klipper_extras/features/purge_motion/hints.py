"""Collect purge hints from live Klipper objects."""

from __future__ import annotations

from ... import klipper_fields as kf
from ...constants import extra_object, heat_floor_from_min_extrude_temp
from .types import PurgeKlipperHints


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
    retract, retract_speed = kf.firmware_retract(printer)
    ax_min_x, ax_min_y, ax_max_x, ax_max_y = kf.axis_xy_limits(printer)
    return PurgeKlipperHints(
        max_velocity=kf.max_velocity(printer),
        min_nozzle_temp=heat_floor_from_min_extrude_temp(
            kf.min_extrude_temp(printer)
        ),
        host_min_nozzle_temp=host_min_nozzle_temp_from_host(
            printer.lookup_object(extra_object(), None)
        ),
        retract=retract,
        retract_speed=retract_speed,
        z_hop=kf.safe_z_hop(printer),
        fan=kf.default_fan(printer),
        filament_diameter=kf.filament_diameter(printer),
        max_extrude_cross_section=kf.max_extrude_cross_section(printer),
        max_extrude_only_velocity=kf.max_extrude_only_velocity(printer),
        axis_minimum_x=ax_min_x,
        axis_minimum_y=ax_min_y,
        axis_maximum_x=ax_max_x,
        axis_maximum_y=ax_max_y,
    )


def collect_object_aabb(printer):
    """Return (x_min, y_min, x_max, y_max) from exclude_object, or None."""
    eo = printer.lookup_object("exclude_object", None)
    if eo is None:
        return None
    try:
        st = eo.get_status(kf.eventtime(printer))
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
