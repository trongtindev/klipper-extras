"""Resolve form_tip settings: user → profile → hint. Pure, no Klipper imports."""

from __future__ import annotations

from dataclasses import replace as dataclass_replace
from typing import Optional

from . import messages as msg
from .constants import PARAM_ALIASES, PROFILES
from .types import FormTipHints, FormTipProfile, FormTipSettings, FormTipStep


def _present(user: dict, key: str) -> bool:
    if key not in user:
        return False
    val = user[key]
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True


def _as_float(raw, key: str) -> float:
    if isinstance(raw, bool):
        raise ValueError(msg.invalid_number(key, raw))
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError) as e:
        raise ValueError(msg.invalid_number(key, raw)) from e


def _as_int(raw, key: str) -> int:
    value = _as_float(raw, key)
    if value != int(value):
        raise ValueError(msg.invalid_int(key, raw))
    return int(value)


def _as_bool(raw, key: str) -> bool:
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes"):
        return True
    if s in ("0", "false", "no"):
        return False
    raise ValueError(msg.invalid_bool(key, raw))


def _pick_float(
    profile: FormTipProfile, user: dict, key: str, hint: Optional[float] = None
) -> float:
    if _present(user, key):
        return _as_float(user[key], key)
    # profile has a default; hint only overrides None-worthy fields
    return float(getattr(profile, key))


def _pick_int(
    profile: FormTipProfile, user: dict, key: str
) -> int:
    if _present(user, key):
        return _as_int(user[key], key)
    return int(getattr(profile, key))


def _pick_bool(
    profile: FormTipProfile, user: dict, key: str
) -> bool:
    if _present(user, key):
        return _as_bool(user[key], key)
    return bool(getattr(profile, key))


def _pick_optional_float(
    profile: FormTipProfile,
    user: dict,
    key: str,
    hint: Optional[float] = None,
) -> Optional[float]:
    if _present(user, key):
        return _as_float(user[key], key)
    if hint is not None:
        return float(hint)
    return getattr(profile, key)


def _pick_optional_str(
    profile: FormTipProfile,
    user: dict,
    key: str,
    hint: Optional[str] = None,
) -> Optional[str]:
    if _present(user, key):
        return str(user[key]).strip()
    if hint is not None:
        return str(hint)
    return getattr(profile, key)


def _clamp_speed(value: float, max_velocity: Optional[float]) -> float:
    if max_velocity is not None and max_velocity > 0:
        return min(value, max_velocity)
    return value


def _resolve_profile_name(
    user: dict, known_profiles: dict
) -> Optional[str]:
    """Return the profile name from user, or None."""
    if _present(user, "profile"):
        name = str(user["profile"]).strip().lower()
        if name not in known_profiles:
            raise ValueError(
                msg.unknown_profile(name, ", ".join(sorted(known_profiles)))
            )
        return name
    return None


def resolve_tip_settings(
    kind: str,
    gcode: str,
    user: dict,
    hints: Optional[FormTipHints],
) -> FormTipSettings:
    """Resolve user → profile → hint → settings. Raises ValueError on bad input."""
    known = PROFILES
    profile_name = _resolve_profile_name(user, known)
    if profile_name is not None:
        profile = known[profile_name]
    else:
        profile = FormTipProfile()  # all defaults, but tip_distance must be user-set

    # Resolve each field
    tip_distance = _pick_float(profile, user, "tip_distance")
    unloading_speed_start_len = _pick_float(profile, user, "unloading_speed_start_len")
    unloading_speed_start = _pick_float(profile, user, "unloading_speed_start")
    ramming_len = _pick_float(profile, user, "ramming_len")
    ramming_speed = _pick_float(profile, user, "ramming_speed")
    sep_fast_len = _pick_float(profile, user, "sep_fast_len")
    sep_fast_speed = _pick_float(profile, user, "sep_fast_speed")
    sep_slow_speed = _pick_float(profile, user, "sep_slow_speed")
    cooling_moves = _pick_int(profile, user, "cooling_moves")
    cool_len = _pick_float(profile, user, "cool_len")
    cool_speed_slow = _pick_float(profile, user, "cool_speed_slow")
    cool_speed_fast = _pick_float(profile, user, "cool_speed_fast")
    use_skinnydip = _pick_bool(profile, user, "use_skinnydip")
    dip_in = _pick_float(profile, user, "dip_in")
    dip_in_speed = _pick_float(profile, user, "dip_in_speed")
    dip_out_speed = _pick_float(profile, user, "dip_out_speed")
    pause_melt_ms = _pick_int(profile, user, "pause_melt_ms")
    pause_cool_ms = _pick_int(profile, user, "pause_cool_ms")
    parking_distance = _pick_float(profile, user, "parking_distance")
    park_speed = _pick_float(profile, user, "park_speed")
    fan_speed = _pick_float(profile, user, "fan_speed")
    fan = _pick_optional_str(profile, user, "fan", hints.fan if hints else None)
    min_nozzle_temp = _pick_optional_float(
        profile, user, "min_nozzle_temp", hints.min_nozzle_temp if hints else None
    )
    nozzle_temperature = _pick_optional_float(profile, user, "nozzle_temperature")

    # Clamp speeds to max_extrude_only_velocity hint
    max_vel = hints.max_extrude_only_velocity if hints else None
    unloading_speed_start = _clamp_speed(unloading_speed_start, max_vel)
    ramming_speed = _clamp_speed(ramming_speed, max_vel)
    sep_fast_speed = _clamp_speed(sep_fast_speed, max_vel)
    sep_slow_speed = _clamp_speed(sep_slow_speed, max_vel)
    cool_speed_slow = _clamp_speed(cool_speed_slow, max_vel)
    cool_speed_fast = _clamp_speed(cool_speed_fast, max_vel)
    dip_in_speed = _clamp_speed(dip_in_speed, max_vel)
    dip_out_speed = _clamp_speed(dip_out_speed, max_vel)
    park_speed = _clamp_speed(park_speed, max_vel)

    return FormTipSettings(
        kind=kind,
        gcode=gcode,
        profile_name=profile_name,
        tip_distance=tip_distance,
        unloading_speed_start_len=unloading_speed_start_len,
        unloading_speed_start=unloading_speed_start,
        ramming_len=ramming_len,
        ramming_speed=ramming_speed,
        sep_fast_len=sep_fast_len,
        sep_fast_speed=sep_fast_speed,
        sep_slow_speed=sep_slow_speed,
        cooling_moves=cooling_moves,
        cool_len=cool_len,
        cool_speed_slow=cool_speed_slow,
        cool_speed_fast=cool_speed_fast,
        use_skinnydip=use_skinnydip,
        dip_in=dip_in,
        dip_in_speed=dip_in_speed,
        dip_out_speed=dip_out_speed,
        pause_melt_ms=pause_melt_ms,
        pause_cool_ms=pause_cool_ms,
        parking_distance=parking_distance,
        park_speed=park_speed,
        fan_speed=fan_speed,
        fan=fan,
        min_nozzle_temp=min_nozzle_temp,
        nozzle_temperature=nozzle_temperature,
    )


def _gcode_float(label: str, value: float) -> str:
    return "%.3f" % (value,)


def _gcode_speed(speed_mms: float) -> str:
    return "F%.0f" % (speed_mms * 60.0,)


def _emit_extrude(delta: float, speed: float, label: str) -> Optional[FormTipStep]:
    """G1 E{delta} F{speed*60} in relative extrusion mode."""
    if delta == 0:
        return None
    return FormTipStep(
        command="G1 E%s %s" % (_gcode_float("E", delta), _gcode_speed(speed)),
        label=label,
    )


def _fan_on_command(settings: FormTipSettings) -> str:
    """Generate M106 or SET_FAN_SPEED command."""
    if settings.fan is None or settings.fan_speed <= 0:
        return ""
    if settings.fan == "fan":
        return "M106 S%.0f" % (settings.fan_speed * 255.0,)
    return "SET_FAN_SPEED FAN=%s SPEED=%.3f" % (settings.fan, settings.fan_speed)


def plan_tip_steps(settings: FormTipSettings) -> list[FormTipStep]:
    """Plan all G-code steps for one FORM_TIP execution."""
    steps: list[FormTipStep] = []

    # Phase 0: Heat wait — handled at runner level, not as G-code step here
    # (runner uses M109 directly, not script-from-command)

    # Phase 1: Unloading speed start
    step = _emit_extrude(
        -settings.unloading_speed_start_len,
        settings.unloading_speed_start,
        "unload_start",
    )
    if step:
        steps.append(step)

    # Phase 2: Separation
    step = _emit_extrude(-settings.sep_fast_len, settings.sep_fast_speed, "sep_fast")
    if step:
        steps.append(step)
    sep_slow = settings.sep_slow_len
    if sep_slow > 0:
        steps.append(
            _emit_extrude(-sep_slow, settings.sep_slow_speed, "sep_slow")
        )

    # Phase 4: Ramming
    step = _emit_extrude(settings.ramming_len, settings.ramming_speed, "ramming")
    if step:
        steps.append(step)

    # Phase 3+5: Fan ON + Cooling moves (fan helps cool the tip during cooling)
    fan_cmd = _fan_on_command(settings)
    if fan_cmd:
        steps.append(FormTipStep(command=fan_cmd, label="fan_on"))
    n = settings.cooling_moves
    if n > 0:
        cool_len = settings.cool_len
        slow = settings.cool_speed_slow
        fast = settings.cool_speed_fast
        if n == 1:
            # Single move pair — both at slow speed
            steps.append(
                FormTipStep(
                    command="G1 E%s %s\nG1 E-%s %s"
                    % (
                        _gcode_float("E", cool_len),
                        _gcode_speed(slow),
                        _gcode_float("E", cool_len),
                        _gcode_speed(slow),
                    ),
                    label="cool_0",
                )
            )
        else:
            speed_inc = (fast - slow) / (2 * n - 1)
            for move in range(n):
                speed = slow + speed_inc * move * 2
                step_speed = speed + speed_inc
                steps.append(
                    FormTipStep(
                        command="G1 E%s %s\nG1 E-%s %s"
                        % (
                            _gcode_float("E", cool_len),
                            _gcode_speed(speed),
                            _gcode_float("E", cool_len),
                            _gcode_speed(step_speed),
                        ),
                        label="cool_%d" % (move,),
                    )
                )

    # Phase 6: Skinnydip
    if settings.use_skinnydip:
        parts = []
        parts.append("G1 E%s %s" % (
            _gcode_float("E", settings.dip_in),
            _gcode_speed(settings.dip_in_speed),
        ))
        if settings.pause_melt_ms > 0:
            parts.append("G4 P%d" % (settings.pause_melt_ms,))
        parts.append("G1 E-%s %s" % (
            _gcode_float("E", settings.dip_in),
            _gcode_speed(settings.dip_out_speed),
        ))
        if settings.pause_cool_ms > 0:
            parts.append("G4 P%d" % (settings.pause_cool_ms,))
        steps.append(FormTipStep(command="\n".join(parts), label="skinnydip"))

    # Phase 7: Parking
    if settings.parking_distance != 0:
        steps.append(
            FormTipStep(
                command="G1 E-%s %s"
                % (
                    _gcode_float("E", abs(settings.parking_distance)),
                    _gcode_speed(settings.park_speed),
                ),
                label="parking",
            )
        )

    return steps


def overlay_gcode_params(
    gcmd,
    settings: FormTipSettings,
) -> FormTipSettings:
    """Apply G-code param overrides to a copy of settings. Returns new settings."""
    overrides = {}
    # Try full UPPER_SNAKE_CASE for each field
    for key_long in settings.__class__.__dataclass_fields__:
        gcode_key = _to_gcode_key(key_long)
        val = gcmd.get(gcode_key, None)
        if val is not None:
            overrides[key_long] = val
    # Try aliases
    for alias, key_long in PARAM_ALIASES.items():
        val = gcmd.get(alias, None)
        if val is not None:
            overrides[key_long] = val

    if not overrides:
        return settings

    # Parse and clamp override values
    parsed = {}
    for key, raw in overrides.items():
        if key in ("use_skinnydip",):
            parsed[key] = _as_bool(raw, key)
        elif key in ("cooling_moves", "pause_melt_ms", "pause_cool_ms"):
            parsed[key] = _as_int(raw, key)
        elif key in ("fan", "profile"):
            parsed[key] = str(raw).strip()
        elif key in ("min_nozzle_temp", "nozzle_temperature"):
            if raw is None or str(raw).strip() == "":
                parsed[key] = None
            else:
                parsed[key] = _as_float(raw, key)
        else:
            parsed[key] = _as_float(raw, key)

    # Clamp speed fields
    for key in (
        "unloading_speed_start", "ramming_speed", "sep_fast_speed",
        "sep_slow_speed", "cool_speed_slow", "cool_speed_fast",
        "dip_in_speed", "dip_out_speed", "park_speed",
    ):
        if key in parsed:
            parsed[key] = _clamp_speed(parsed[key], None)

    return dataclass_replace(settings, **parsed)


def _to_gcode_key(key: str) -> str:
    """Convert 'nozzle_temperature' to 'NOZZLE_TEMPERATURE'."""
    return key.upper()
