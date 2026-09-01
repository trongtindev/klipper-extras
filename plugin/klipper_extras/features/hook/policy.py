"""Pure on_hook_fail resolve. No Klipper imports."""

from __future__ import annotations

from typing import Optional

from .constants import DEFAULT_ON_HOOK_FAIL, ON_FAIL_CHOICES
from .messages import invalid_on_hook_fail


def is_hook_config_key(key: str) -> bool:
    """True for template / fail-policy keys (not path or tip geometry)."""
    return key == "on_hook_fail" or key.endswith("_gcode")


def hook_option_keys_for_actions(actions) -> frozenset:
    """before_<action>_gcode / after_<action>_gcode / on_hook_fail for one feature."""
    keys = ["on_hook_fail"]
    for action in actions:
        keys.append("before_%s_gcode" % (action,))
        keys.append("after_%s_gcode" % (action,))
    return frozenset(keys)


def resolve_on_hook_fail(raw: Optional[object] = None) -> str:
    """Return stop|continue. Omitted/empty → stop. Unknown → ValueError."""
    if raw is None:
        return DEFAULT_ON_HOOK_FAIL
    text = str(raw).strip().lower()
    if text == "":
        return DEFAULT_ON_HOOK_FAIL
    if text not in ON_FAIL_CHOICES:
        raise ValueError(invalid_on_hook_fail(raw))
    return text
