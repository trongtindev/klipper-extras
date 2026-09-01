"""Live Klipper field reads (attribute names from klippy)."""

import math

import pytest

from klipper_extras.constants import MIN_EXTRUDE_TEMP_HEAT_MARGIN
from klipper_extras.features.purge_motion.hints import collect_purge_hints
from klipper_extras.features.wipe_motion.hints import collect_wipe_hints
from klipper_extras.klipper_fields import (
    axis_xy_limits,
    filament_diameter,
    max_extrude_cross_section,
    max_extrude_only_velocity,
    max_velocity,
    min_extrude_temp,
)


class _PrinterConfig:
    """Shape of klippy ``PrinterConfig`` (status_raw_config, no fileconfig)."""

    def __init__(self, raw=None):
        self.status_raw_config = raw or {}


class _Heater:
    def __init__(self, min_extrude_temp=170.0):
        self.min_extrude_temp = min_extrude_temp


class _Extruder:
    """Shape of klippy ``PrinterExtruder``."""

    def __init__(
        self,
        diameter=1.75,
        nozzle=0.4,
        max_e_velocity=42.0,
        heater=None,
    ):
        self.filament_area = math.pi * (diameter * 0.5) ** 2
        self.max_extrude_ratio = (4.0 * nozzle**2) / self.filament_area
        self.max_e_velocity = max_e_velocity
        self.heater = heater if heater is not None else _Heater()

    def get_heater(self):
        return self.heater


class _Toolhead:
    def __init__(self, vel=250.0, accel=3000.0, xmin=0.0, ymin=10.0, xmax=220.0, ymax=220.0):
        self._vel = vel
        self._accel = accel
        self._min = _Coord(xmin, ymin)
        self._max = _Coord(xmax, ymax)

    def get_max_velocity(self):
        return self._vel, self._accel

    def get_status(self, eventtime):
        return {
            "max_velocity": self._vel,
            "axis_minimum": self._min,
            "axis_maximum": self._max,
        }


class _Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class _Reactor:
    def monotonic(self):
        return 0.0


class _Printer:
    def __init__(self, objects):
        self._objects = objects

    def lookup_object(self, name, default=None):
        return self._objects.get(name, default)

    def get_reactor(self):
        return _Reactor()


def test_min_extrude_temp_from_heater_when_key_present():
    printer = _Printer(
        {
            "extruder": _Extruder(heater=_Heater(185.0)),
            "configfile": _PrinterConfig({"extruder": {"min_extrude_temp": "185"}}),
        }
    )
    assert min_extrude_temp(printer) == 185.0


def test_min_extrude_temp_skipped_without_config_key():
    printer = _Printer(
        {
            "extruder": _Extruder(heater=_Heater(170.0)),
            "configfile": _PrinterConfig({"extruder": {"filament_diameter": "1.75"}}),
        }
    )
    assert min_extrude_temp(printer) is None


def test_filament_diameter_from_filament_area():
    printer = _Printer({"extruder": _Extruder(diameter=1.75)})
    assert filament_diameter(printer) == pytest.approx(1.75)


def test_filament_diameter_none_without_extruder():
    assert filament_diameter(_Printer({})) is None


def test_max_e_velocity_attr():
    printer = _Printer({"extruder": _Extruder(max_e_velocity=42.0)})
    assert max_extrude_only_velocity(printer) == 42.0


def test_max_extrude_cross_section_from_ratio_and_area():
    extruder = _Extruder(diameter=1.75, nozzle=0.4)
    printer = _Printer({"extruder": extruder})
    assert max_extrude_cross_section(printer) == pytest.approx(
        extruder.max_extrude_ratio * extruder.filament_area
    )


def test_max_velocity_from_get_max_velocity():
    printer = _Printer({"toolhead": _Toolhead(vel=250.0)})
    assert max_velocity(printer) == 250.0


def test_axis_xy_limits_from_coord():
    printer = _Printer({"toolhead": _Toolhead(xmin=0.0, ymin=10.0, xmax=220.0, ymax=220.0)})
    assert axis_xy_limits(printer) == (0.0, 10.0, 220.0, 220.0)


def test_collect_wipe_hints_klippy_shaped():
    printer = _Printer(
        {
            "toolhead": _Toolhead(vel=300.0),
            "extruder": _Extruder(heater=_Heater(190.0)),
            "configfile": _PrinterConfig({"extruder": {"min_extrude_temp": "190"}}),
            "fan": object(),
        }
    )
    hints = collect_wipe_hints(printer)
    assert hints.max_velocity == 300.0
    assert hints.min_nozzle_temp == 190.0 + MIN_EXTRUDE_TEMP_HEAT_MARGIN
    assert hints.fan == "fan"


def test_collect_purge_hints_klippy_shaped():
    printer = _Printer(
        {
            "toolhead": _Toolhead(vel=300.0, xmin=0.0, ymin=0.0, xmax=250.0, ymax=210.0),
            "extruder": _Extruder(diameter=1.75, max_e_velocity=55.0, heater=_Heater(185.0)),
            "configfile": _PrinterConfig({"extruder": {"min_extrude_temp": "185"}}),
        }
    )
    hints = collect_purge_hints(printer)
    assert hints.max_velocity == 300.0
    assert hints.min_nozzle_temp == 185.0 + MIN_EXTRUDE_TEMP_HEAT_MARGIN
    assert hints.filament_diameter == pytest.approx(1.75)
    assert hints.max_extrude_only_velocity == 55.0
    assert hints.max_extrude_cross_section == pytest.approx(4.0 * 0.4**2)
    assert hints.axis_minimum_x == 0.0
    assert hints.axis_maximum_y == 210.0
