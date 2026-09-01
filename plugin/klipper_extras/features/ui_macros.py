"""Frontend gcode_macro status objects for action features.

Frontends list printer objects named ``gcode_macro NAME``. Extra commands
registered with ``gcode.register_command`` do not create those objects.
Empty status objects expose the feature G-code on the Macros panel. They
do not handle G-code.

Call after full config load (``klippy:connect``) so a real
``[gcode_macro NAME]`` section is never short-circuited by ``load_object``.
"""

from __future__ import annotations


class UiMacroShim:
    """Empty get_status so frontends list this as a gcode_macro button."""

    def get_status(self, eventtime):
        return {}


def ui_macro_object_name(gcode_name: str) -> str:
    return "gcode_macro %s" % (gcode_name,)


def _object_exists(printer, obj_name: str) -> bool:
    if printer.lookup_object(obj_name, None) is not None:
        return True
    lookup_objects = getattr(printer, "lookup_objects", None)
    if lookup_objects is None:
        return False
    want = obj_name.lower()
    for name, _obj in lookup_objects():
        if str(name).lower() == want:
            return True
    return False


def register_ui_macro_shims(printer, names):
    """Add gcode_macro status shims when no object already exists.

    *names* is an iterable of G-code command names (``PAUSE``,
    ``WIPE_NOZZLE_ON_BED``, …). Returns list of object names registered.
    Existing objects (any case) are skipped with no log.
    """
    registered = []
    for name in names:
        obj_name = ui_macro_object_name(name)
        if _object_exists(printer, obj_name):
            continue
        printer.add_object(obj_name, UiMacroShim())
        registered.append(obj_name)
    return registered
