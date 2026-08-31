"""Field config: user → Klipper hint/calc → profile. Pure, no Klipper imports."""

from __future__ import annotations

from typing import Optional

from . import messages as msg


def present(user: dict, key: str) -> bool:
    if key not in user:
        return False
    val = user[key]
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True


def as_float(raw, key: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(msg.invalid_number(key, raw))
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError) as e:
        raise ValueError(msg.invalid_number(key, raw)) from e


def as_int(raw, key: str) -> int:
    value = as_float(raw, key)
    if value != int(value):
        raise ValueError(msg.invalid_int(key, raw))
    return int(value)


def as_bool(raw, key: str) -> bool:
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no"):
        return False
    raise ValueError(msg.invalid_bool(key, raw))


def pick_bool(user: dict, key: str, profile: bool) -> bool:
    if present(user, key):
        return as_bool(user[key], key)
    return bool(profile)


def pick_float(user: dict, key: str, hint: Optional[float], profile: float) -> float:
    """User key, else Klipper hint/calc, else that owner's profile default."""
    if present(user, key):
        return as_float(user[key], key)
    if hint is not None:
        return float(hint)
    return float(profile)


def pick_int(user: dict, key: str, profile: int) -> int:
    if present(user, key):
        return as_int(user[key], key)
    return int(profile)


def pick_optional_float(user: dict, key: str, hint: Optional[float]) -> Optional[float]:
    if present(user, key):
        return as_float(user[key], key)
    if hint is not None:
        return float(hint)
    return None


def pick_optional_str(
    user: dict, key: str, hint: Optional[str]
) -> Optional[str]:
    if present(user, key):
        name = str(user[key]).strip()
        return name if name else None
    if hint is not None:
        return str(hint)
    return None


def clamp_speed(value: float, max_velocity: Optional[float]) -> float:
    if max_velocity is not None and max_velocity > 0:
        return min(value, max_velocity)
    return value


def pick_speed(
    user: dict,
    key: str,
    hint: Optional[float],
    profile: float,
    max_velocity: Optional[float],
) -> float:
    """User override, else hint (e.g. printer ``max_velocity``), else profile.

    Result is capped at ``max_velocity`` when that field exists.
    """
    return clamp_speed(pick_float(user, key, hint, profile), max_velocity)
