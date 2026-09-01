"""Load hook templates from a Klipper config section (Klipper I/O)."""

from __future__ import annotations

from .constants import (
    DEFAULT_DEBUG,
    DEFAULT_ON_HOOK_FAIL,
    ON_FAIL_CONTINUE,
    ON_FAIL_STOP,
    OPTION_DEBUG,
)
from .execute import EmptyHookTemplate
from .policy import is_hook_config_key


def _gcode_macro(printer, config):
    obj = printer.lookup_object("gcode_macro", None)
    if obj is not None:
        return obj
    load_object = getattr(printer, "load_object", None)
    if load_object is None:
        return None
    return load_object(config, "gcode_macro")


def config_has_option(config, name: str) -> bool:
    try:
        return config.fileconfig.has_option(config.get_name(), name)
    except Exception:
        return False


def parse_user_config(config, option_keys) -> dict:
    """Section keys except hook templates / on_hook_fail."""
    user = {}
    for key in option_keys:
        if is_hook_config_key(key):
            continue
        if config_has_option(config, key):
            user[key] = config.get(key)
    return user


def load_gcode_template(config, printer, option: str):
    """Like probe ``activate_gcode``: ``load_template(config, option, '')``."""
    gcode_macro = _gcode_macro(printer, config)
    if gcode_macro is None:
        return EmptyHookTemplate()
    return gcode_macro.load_template(config, option, "")


def load_on_hook_fail(config) -> str:
    """Klipper ``getchoice`` when present; else default stop."""
    getchoice = getattr(config, "getchoice", None)
    if getchoice is None:
        return DEFAULT_ON_HOOK_FAIL
    return getchoice(
        "on_hook_fail",
        {ON_FAIL_STOP: ON_FAIL_STOP, ON_FAIL_CONTINUE: ON_FAIL_CONTINUE},
        DEFAULT_ON_HOOK_FAIL,
    )


def load_debug(config) -> bool:
    """Klipper ``getboolean`` when present; else default False."""
    getboolean = getattr(config, "getboolean", None)
    if getboolean is None:
        return DEFAULT_DEBUG
    return bool(getboolean(OPTION_DEBUG, DEFAULT_DEBUG))


def load_action_hook_templates(config, printer, actions):
    """Map (action, before|after) → template for each named action."""
    templates = {}
    for action in actions:
        templates[(action, "before")] = load_gcode_template(
            config, printer, "before_%s_gcode" % (action,)
        )
        templates[(action, "after")] = load_gcode_template(
            config, printer, "after_%s_gcode" % (action,)
        )
    return templates
