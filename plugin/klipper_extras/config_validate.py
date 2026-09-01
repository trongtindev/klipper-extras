"""Early config validation for [klipper_extras] (pure logic, no Klipper imports)."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import messages as msg
from .constants import CONFIG_SEVERITY_ERROR, LOG_LEVELS
from .defaults import CommonSettings


@dataclass(frozen=True)
class ConfigIssue:
    severity: str
    message: str


@dataclass
class ValidationResult:
    errors: list[ConfigIssue] = field(default_factory=list)
    warnings: list[ConfigIssue] = field(default_factory=list)


def validate_common_config(settings: CommonSettings) -> ValidationResult:
    """Validate resolved host settings. Empty errors means OK to continue."""
    result = ValidationResult()
    if settings.log_level not in LOG_LEVELS:
        result.errors.append(
            ConfigIssue(
                CONFIG_SEVERITY_ERROR,
                msg.invalid_log_level(settings.log_level),
            )
        )
    return result
