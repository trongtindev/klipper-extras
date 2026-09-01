from klipper_extras.config_validate import validate_common_config
from klipper_extras.defaults import CommonSettings


def test_validate_ok():
    result = validate_common_config(CommonSettings(log_level="info"))
    assert result.errors == []
    assert result.warnings == []


def test_validate_bad_log_level():
    result = validate_common_config(CommonSettings(log_level="nope"))
    assert len(result.errors) == 1
    assert "invalid log_level" in result.errors[0].message
