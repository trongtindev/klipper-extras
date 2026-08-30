"""Owned keys and literals for [klipper_common hook]."""

from __future__ import annotations

KIND = "hook"

# No G-code command. Other features lookup this object.
GCODE = None

ON_FAIL_STOP = "stop"
ON_FAIL_CONTINUE = "continue"
ON_FAIL_CHOICES = (ON_FAIL_STOP, ON_FAIL_CONTINUE)
DEFAULT_ON_HOOK_FAIL = ON_FAIL_STOP

OPTION_COMMAND_BEFORE = "command_before_gcode"
OPTION_COMMAND_AFTER = "command_after_gcode"
OPTION_ON_HOOK_FAIL = "on_hook_fail"
OPTION_DEBUG = "debug"
DEFAULT_DEBUG = False

# Klipper object name for lookup_object (not a G-code).
OBJECT_NAME = "klipper_common hook"

OPTION_KEYS = frozenset(
    (
        OPTION_COMMAND_BEFORE,
        OPTION_COMMAND_AFTER,
        OPTION_ON_HOOK_FAIL,
        OPTION_DEBUG,
    )
)

HOOK_PHASE_BEFORE = "before"
HOOK_PHASE_AFTER = "after"
HOOK_ACTION_COMMAND = "command"
