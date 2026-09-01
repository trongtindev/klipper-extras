"""Validate a resolved wipe path (pure)."""

from __future__ import annotations

from ...config_validate import ConfigIssue, ValidationResult
from ...constants import CONFIG_SEVERITY_ERROR
from . import messages as msg
from .types import WipePathSettings


def validate_path(settings: WipePathSettings) -> ValidationResult:
    result = ValidationResult()
    if settings.wipe_z < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.wipe_z_negative()))
    if settings.z_hop < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.z_hop_negative()))
    if settings.travel_z <= settings.wipe_z:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.travel_z_too_low()))
    if settings.wipe_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("wipe_speed"))
        )
    if settings.travel_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("travel_speed"))
        )
    if settings.passes < 1:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.passes_invalid()))
    if settings.fan_speed < 0.0 or settings.fan_speed > 1.0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.fan_speed_invalid()))
    if settings.retract < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.retract_invalid()))
    if settings.retract > 0 and settings.retract_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("retract_speed"))
        )
    if settings.start_x == settings.end_x and settings.start_y == settings.end_y:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.zero_length()))
    if (
        settings.nozzle_temperature is not None
        and settings.min_nozzle_temp is not None
        and settings.nozzle_temperature < settings.min_nozzle_temp
    ):
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.nozzle_temp_below_min())
        )
    return result
