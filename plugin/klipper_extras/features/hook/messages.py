"""User-facing and log strings for common hook (% formatting)."""

from __future__ import annotations

from ...messages import line
from .constants import ON_FAIL_CHOICES


def invalid_on_hook_fail(value) -> str:
    return line("invalid on_hook_fail %r (choices: %s)", value, ", ".join(ON_FAIL_CHOICES))


def hook_failed_continue(label: str) -> str:
    return line("hook %s failed; on_hook_fail=continue", label)


def hook_debug_call(kind: str, action: str, phase: str, extra=None, empty=False) -> str:
    extra = extra or {}
    if "pass_index" in extra:
        text = line(
            "hook %s %s %s pass_index=%s",
            kind,
            action,
            phase,
            extra["pass_index"],
        )
    else:
        text = line("hook %s %s %s", kind, action, phase)
    if empty:
        return "%s (empty)" % (text,)
    return text
