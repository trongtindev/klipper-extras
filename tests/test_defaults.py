import pytest

from klipper_extras.constants import LOG_LEVEL_DEFAULT, LOG_LEVEL_INFO
from klipper_extras.defaults import resolve_settings


def test_resolve_empty_user_uses_default():
    s = resolve_settings({})
    assert s.log_level == LOG_LEVEL_DEFAULT
    assert s.log_level == LOG_LEVEL_INFO
    assert s.min_nozzle_temp is None


def test_resolve_min_nozzle_temp():
    s = resolve_settings({"min_nozzle_temp": "180"})
    assert s.min_nozzle_temp == 180.0


def test_resolve_invalid_min_nozzle_temp():
    with pytest.raises(ValueError, match="min_nozzle_temp"):
        resolve_settings({"min_nozzle_temp": "hot"})


def test_resolve_explicit_verbose():
    s = resolve_settings({"log_level": "verbose"})
    assert s.log_level == "verbose"


def test_resolve_normalizes_case():
    s = resolve_settings({"log_level": "DEBUG"})
    assert s.log_level == "debug"


def test_resolve_invalid_raises():
    with pytest.raises(ValueError, match="invalid log_level"):
        resolve_settings({"log_level": "loud"})
