"""Validate a resolved purge path (pure)."""

from __future__ import annotations

from ...config_validate import ConfigIssue, ValidationResult
from ...constants import CONFIG_SEVERITY_ERROR
from . import messages as msg
from .constants import ORIGIN_FIXED, STYLE_LINE, STYLE_VORON
from .types import PurgePathSettings


def validate_path(settings: PurgePathSettings) -> ValidationResult:
    result = ValidationResult()
    if settings.purge_z < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.purge_z_negative()))
    if settings.z_hop < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.z_hop_negative()))
    if settings.travel_z <= settings.purge_z:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.travel_z_too_low()))
    if settings.travel_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("travel_speed"))
        )
    if settings.flow_rate <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("flow_rate"))
        )
    if settings.purge_amount <= 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.amount_not_positive()))
    if settings.filament_diameter <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.filament_diameter_invalid())
        )
    if settings.fan_speed < 0.0 or settings.fan_speed > 1.0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.fan_speed_invalid()))
    if settings.retract < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.retract_invalid()))
    if settings.retract > 0 and settings.retract_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("retract_speed"))
        )
    if settings.tip_distance < 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.tip_distance_invalid())
        )
    if settings.move_while_purge and settings.style == STYLE_LINE:
        if settings.purge_length is None or settings.purge_length <= 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.length_not_positive())
            )
    if settings.move_while_purge and settings.style == STYLE_VORON:
        if settings.style_size is None or settings.style_size <= 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.style_size_not_positive())
            )
    if settings.origin_mode == ORIGIN_FIXED:
        if settings.start_x is None or settings.start_y is None:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.origin_not_resolved())
            )
    if settings.min_nozzle_temp is None and settings.nozzle_temperature is None:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.heat_temp_required(settings.kind))
        )
    if (
        settings.nozzle_temperature is not None
        and settings.min_nozzle_temp is not None
        and settings.nozzle_temperature < settings.min_nozzle_temp
    ):
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.nozzle_temp_below_min())
        )
    return result
