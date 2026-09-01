"""Owned keys, profiles, and aliases for form_tip."""

from __future__ import annotations

from ..hook.policy import hook_option_keys_for_actions
from .messages import help_form_tip
from .types import FormTipProfile

KIND = "form_tip"
GCODE = "FORM_TIP"

FORM_TIP_HOOK_ACTIONS = (
    "heat",
    "unload_start",
    "sep_fast",
    "sep_slow",
    "ramming",
    "fan",
    "cool",
    "skinnydip",
    "parking",
)


OPTION_KEYS = frozenset(
    (
        "profile",
        "unloading_speed_start_len",
        "unloading_speed_start",
        "ramming_len",
        "ramming_speed",
        "tip_distance",
        "sep_fast_len",
        "sep_fast_speed",
        "sep_slow_speed",
        "cooling_moves",
        "cool_len",
        "cool_speed_slow",
        "cool_speed_fast",
        "use_skinnydip",
        "dip_in",
        "dip_in_speed",
        "dip_out_speed",
        "pause_melt_ms",
        "pause_cool_ms",
        "parking_distance",
        "park_speed",
        "fan_speed",
        "fan",
        "nozzle_temperature",
        "min_nozzle_temp",
    )
) | hook_option_keys_for_actions(FORM_TIP_HOOK_ACTIONS)

# Built-in profiles. profile key in config selects one; individual keys override.
# a4t_hgx_lite matches the numbers from _FORM_TIP_VARS (original config).
PROFILES = {
    "a4t_hgx_lite": FormTipProfile(
        unloading_speed_start=80.0,
        ramming_speed=30.0,
        tip_distance=35.1,
        sep_fast_len=6.0,
        sep_fast_speed=70.0,
        sep_slow_speed=15.0,
        cooling_moves=4,
        cool_len=10.0,
        cool_speed_slow=12.0,
        cool_speed_fast=45.0,
        dip_in=28.0,
        dip_in_speed=25.0,
        dip_out_speed=60.0,
        park_speed=25.0,
    ),
}

# G-code param aliases: short name → internal key.
# Full UPPER_SNAKE_CASE of the key is always supported as well.
PARAM_ALIASES = {
    "NOZZLE_TEMP": "nozzle_temperature",
    "MIN_NOZZLE": "min_nozzle_temp",
    "UNLOAD_START_LEN": "unloading_speed_start_len",
    "UNLOAD_START": "unloading_speed_start",
    "SEP_FAST": "sep_fast_len",
    "COOL": "cool_len",
    "FAN": "fan",
}

# G-code wrap commands
CMD_ABSOLUTE = "G90"
CMD_EXTRUDE_ABS = "M83"
CMD_SAVE_STATE_FORM_TIP = "SAVE_GCODE_STATE NAME=FORM_TIP"
CMD_RESTORE_STATE_FORM_TIP = "RESTORE_GCODE_STATE NAME=FORM_TIP"

HELP_TEXT = help_form_tip()
