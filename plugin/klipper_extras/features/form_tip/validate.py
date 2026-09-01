"""Validate resolved form_tip settings (pure)."""

from __future__ import annotations

from ...config_validate import ConfigIssue, ValidationResult
from ...constants import CONFIG_SEVERITY_ERROR
from . import messages as msg
from .types import FormTipSettings


def validate_tip(settings: FormTipSettings) -> ValidationResult:
    """Validate resolved tip settings. Empty errors means OK."""
    result = ValidationResult()

    if settings.tip_distance <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.tip_distance_required())
        )

    if settings.unloading_speed_start_len > 0 and settings.unloading_speed_start <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("unloading_speed_start"))
        )

    if settings.sep_fast_len > 0 and settings.sep_fast_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("sep_fast_speed"))
        )

    if settings.sep_slow_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("sep_slow_speed"))
        )

    if settings.ramming_len > 0 and settings.ramming_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("ramming_speed"))
        )

    if settings.cooling_moves > 0 and settings.cool_speed_slow <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("cool_speed_slow"))
        )

    if settings.cooling_moves > 0 and settings.cool_speed_fast <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("cool_speed_fast"))
        )

    if settings.use_skinnydip:
        if settings.dip_in_speed <= 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("dip_in_speed"))
            )
        if settings.dip_out_speed <= 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("dip_out_speed"))
            )
        if settings.dip_in <= 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.dip_in_needed())
            )

    if settings.parking_distance != 0 and settings.park_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("park_speed"))
        )

    if settings.fan_speed > 0 and settings.fan is None:
        # fan object not resolved — not a hard error, just no fan available
        pass

    if settings.fan_speed < 0.0 or settings.fan_speed > 1.0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.fan_speed_invalid())
        )

    if (
        settings.nozzle_temperature is not None
        and settings.min_nozzle_temp is not None
        and settings.nozzle_temperature < settings.min_nozzle_temp
    ):
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.nozzle_temp_below_min())
        )

    # Length validations
    for key, val in (
        ("unloading_speed_start_len", settings.unloading_speed_start_len),
        ("ramming_len", settings.ramming_len),
        ("sep_fast_len", settings.sep_fast_len),
        ("tip_distance", settings.tip_distance),
        ("dip_in", settings.dip_in),
    ):
        if val < 0:
            result.errors.append(
                ConfigIssue(CONFIG_SEVERITY_ERROR, msg.length_invalid(key, val))
            )

    if settings.cooling_moves < 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.cooling_moves_invalid())
        )

    if settings.cooling_moves > 0 and settings.cool_len <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.cool_len_needed())
        )

    # sep must not exceed tip_distance
    combined_sep = settings.unloading_speed_start_len + settings.sep_fast_len
    if combined_sep > settings.tip_distance:
        result.errors.append(
            ConfigIssue(
                CONFIG_SEVERITY_ERROR,
                msg.sep_too_long(
                    settings.sep_fast_len,
                    settings.unloading_speed_start_len,
                    settings.tip_distance,
                ),
            )
        )

    return result
