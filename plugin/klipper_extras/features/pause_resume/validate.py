"""Validate resolved pause_resume settings (pure)."""

from __future__ import annotations

from ...config_validate import ConfigIssue, ValidationResult
from ...constants import CONFIG_SEVERITY_ERROR
from . import messages as msg
from .types import PauseResumeSettings


def validate_pause(settings: PauseResumeSettings) -> ValidationResult:
    result = ValidationResult()
    if settings.z_hop < 0:
        result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.z_hop_negative()))
    if settings.travel_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("travel_speed"))
        )
    if settings.z_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("z_speed"))
        )
    for key, value in (
        ("retract", settings.retract),
        ("retract_speed", settings.retract_speed),
        ("unretract", settings.unretract),
        ("unretract_speed", settings.unretract_speed),
        ("cancel_retract", settings.cancel_retract),
    ):
        if value < 0:
            result.errors.append(ConfigIssue(CONFIG_SEVERITY_ERROR, msg.length_invalid(key)))
    if settings.retract > 0 and settings.retract_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("retract_speed"))
        )
    if settings.unretract > 0 and settings.unretract_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("unretract_speed"))
        )
    if settings.cancel_retract > 0 and settings.retract_speed <= 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.speed_not_positive("retract_speed"))
        )
    if settings.idle_timeout < 0:
        result.errors.append(
            ConfigIssue(CONFIG_SEVERITY_ERROR, msg.idle_timeout_invalid())
        )
    if settings.park_at_cancel and settings.park_x is None and settings.cancel_park_x is None:
        result.warnings.append(ConfigIssue("warning", msg.park_at_cancel_no_xy()))
    return result
