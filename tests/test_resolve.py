"""Host field resolve: user → Klipper hint → profile."""

import pytest

from klipper_extras.resolve import (
    as_bool,
    as_float,
    clamp_speed,
    pick_bool,
    pick_float,
    pick_optional_str,
    pick_speed,
    present,
)


def test_present_skips_empty():
    assert present({"a": 1}, "a")
    assert not present({}, "a")
    assert not present({"a": None}, "a")
    assert not present({"a": ""}, "a")
    assert not present({"a": "  "}, "a")


def test_pick_float_user_beats_hint_beats_profile():
    assert pick_float({"travel_speed": 120}, "travel_speed", 300.0, 200.0) == 120.0
    assert pick_float({}, "travel_speed", 300.0, 200.0) == 300.0
    assert pick_float({}, "travel_speed", None, 200.0) == 200.0


def test_pick_speed_uses_printer_max_then_user_override():
    assert pick_speed({}, "travel_speed", 300.0, 200.0, 300.0) == 300.0
    assert pick_speed({"travel_speed": 150}, "travel_speed", 300.0, 200.0, 300.0) == 150.0
    assert pick_speed({"travel_speed": 400}, "travel_speed", 300.0, 200.0, 300.0) == 300.0
    assert pick_speed({}, "travel_speed", None, 200.0, None) == 200.0


def test_pick_speed_caps_profile_wipe_speed():
    assert pick_speed({}, "wipe_speed", None, 80.0, 40.0) == 40.0
    assert pick_speed({"wipe_speed": 25}, "wipe_speed", None, 80.0, 40.0) == 25.0


def test_as_float_rejects_bool():
    with pytest.raises(ValueError, match="travel_speed"):
        as_float(True, "travel_speed")


def test_clamp_speed_ignores_missing_max():
    assert clamp_speed(80.0, None) == 80.0
    assert clamp_speed(80.0, 0.0) == 80.0


def test_pick_bool():
    assert pick_bool({"park_at_cancel": True}, "park_at_cancel", False) is True
    assert pick_bool({"park_at_cancel": "yes"}, "park_at_cancel", False) is True
    assert pick_bool({}, "park_at_cancel", False) is False
    with pytest.raises(ValueError, match="park_at_cancel"):
        as_bool("maybe", "park_at_cancel")


def test_pick_optional_str_fan():
    assert pick_optional_str({"fan": "hotend_fan"}, "fan", "fan") == "hotend_fan"
    assert pick_optional_str({}, "fan", "fan") == "fan"
    assert pick_optional_str({}, "fan", None) is None
    assert pick_optional_str({"fan": ""}, "fan", "fan") == "fan"
