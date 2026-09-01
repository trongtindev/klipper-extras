"""Run one G-code hook template from a command handler (Klipper I/O)."""

from __future__ import annotations

import logging

from .constants import (
    HOOK_PHASE_AFTER,
    HOOK_PHASE_BEFORE,
    OBJECT_NAME,
    ON_FAIL_CONTINUE,
)
from .messages import hook_debug_call, hook_failed_continue


class EmptyHookTemplate:
    """No-op when gcode_macro is unavailable (unit tests)."""

    def render(self, context=None) -> str:
        return ""


def hook_context(printer, kind: str, action: str, phase: str, extra=None) -> dict:
    """Jinja context for one hook. ``kind`` is the action feature kind."""
    gcode_macro = printer.lookup_object("gcode_macro", None)
    if gcode_macro is not None and hasattr(gcode_macro, "create_template_context"):
        context = gcode_macro.create_template_context()
    else:
        context = {}
    context.update({"kind": kind, "action": action, "hook": phase})
    if extra:
        context.update(extra)
    return context


def lookup_common_hook(printer):
    return printer.lookup_object(OBJECT_NAME, None)


def _debug_enabled(printer) -> bool:
    common = lookup_common_hook(printer)
    return bool(common is not None and getattr(common, "debug", False))


def run_hook_template(printer, template, on_hook_fail: str, context, label: str) -> None:
    """Render and run nested G-code. Empty render is a no-op.

    ``command_error`` from **render** (``action_raise_error``) and from nested
    G-code is caught only when ``on_hook_fail`` is continue. Do not swallow
    internal errors. Call only from a G-code command
    (``run_script_from_command``), never ``run_script``.
    """
    _run_hook(printer, template, on_hook_fail, context, label, debug=False)


def _run_hook(
    printer,
    template,
    on_hook_fail: str,
    context,
    label: str,
    debug: bool,
    kind: str = "",
    action: str = "",
    phase: str = "",
    extra=None,
) -> None:
    gcode = printer.lookup_object("gcode")
    error_type = getattr(printer, "command_error", None)

    def _render_and_run() -> None:
        script = "" if template is None else template.render(context)
        empty = not str(script).strip()
        if debug:
            gcode.respond_info(
                hook_debug_call(kind, action, phase, extra, empty=empty)
            )
        if empty:
            return
        gcode.run_script_from_command(script)

    if error_type is None:
        _render_and_run()
        return
    try:
        _render_and_run()
    except error_type:
        if on_hook_fail == ON_FAIL_CONTINUE:
            logging.warning("%s", hook_failed_continue(label))
            return
        raise


def call_hook(
    printer,
    template,
    on_hook_fail: str,
    kind: str,
    action: str,
    phase: str,
    extra=None,
) -> None:
    """One hook invoke: debug log (if enabled, including empty), then render+run.

    Action features and ``[klipper_extras hook]`` both use this. Do not
    duplicate context / debug / run in feature runners.
    """
    _run_hook(
        printer,
        template,
        on_hook_fail,
        hook_context(printer, kind, action, phase, extra),
        "%s %s" % (action, phase),
        debug=_debug_enabled(printer),
        kind=kind,
        action=action,
        phase=phase,
        extra=extra,
    )


def call_action_hook(
    printer,
    templates: dict,
    on_hook_fail: str,
    kind: str,
    action: str,
    phase: str,
    extra=None,
) -> None:
    """Feature-owned before/after template for one named action."""
    call_hook(
        printer,
        templates.get((action, phase)),
        on_hook_fail,
        kind,
        action,
        phase,
        extra,
    )


def run_hooked_action(
    printer,
    templates: dict,
    on_hook_fail: str,
    kind: str,
    action: str,
    work,
    extra=None,
):
    """before → work → after. Returns ``work()``."""
    call_action_hook(
        printer, templates, on_hook_fail, kind, action, HOOK_PHASE_BEFORE, extra
    )
    result = work()
    call_action_hook(
        printer, templates, on_hook_fail, kind, action, HOOK_PHASE_AFTER, extra
    )
    return result


def bind_hooked(printer, templates: dict, on_hook_fail: str, kind: str):
    """Bind ``run_hooked_action`` to one feature instance. Replaces per-runner ``_hooked``."""

    def hooked(action: str, work, extra=None):
        return run_hooked_action(
            printer, templates, on_hook_fail, kind, action, work, extra
        )

    return hooked


def call_common_hook(printer, phase: str, extra=None) -> None:
    """Command wrap from ``[klipper_extras hook]`` if that extra is loaded."""
    common = lookup_common_hook(printer)
    if common is None:
        return
    extra = extra or {}
    if phase == HOOK_PHASE_BEFORE:
        common.run_command_before(extra)
        return
    if phase == HOOK_PHASE_AFTER:
        common.run_command_after(extra)
        return
    raise ValueError("unknown hook phase %r" % (phase,))
