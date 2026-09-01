"""Collect wipe hints from live Klipper objects."""

from __future__ import annotations

from ... import klipper_fields as kf
from ...constants import heat_floor_from_min_extrude_temp
from .types import WipeKlipperHints


def collect_wipe_hints(printer) -> WipeKlipperHints:
    """Read live Klipper objects. Missing objects stay None."""
    retract, retract_speed = kf.firmware_retract(printer)
    return WipeKlipperHints(
        max_velocity=kf.max_velocity(printer),
        min_nozzle_temp=heat_floor_from_min_extrude_temp(
            kf.min_extrude_temp(printer)
        ),
        retract=retract,
        retract_speed=retract_speed,
        z_hop=kf.safe_z_hop(printer),
        fan=kf.default_fan(printer),
    )
