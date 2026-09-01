"""Require or warn on Klipper extras. Duck-type lookup_object; no klippy import.

Features declare object names. This module is the only existence check.
Do not scatter lookup_object just to see whether an extra is loaded.
"""

from __future__ import annotations

import logging

from . import messages as msg
from .constants import extra_object


def lookup_component(printer, name: str):
    return printer.lookup_object(name, None)


def missing_components(printer, names) -> list:
    """Names not loaded, in declaration order."""
    missing = []
    for name in names:
        if lookup_component(printer, name) is None:
            missing.append(name)
    return missing


def _raise_config(printer, text: str) -> None:
    raise printer.config_error(text)


def check_components(printer, kind: str, required=(), optional=()) -> dict:
    """Map name → object. Required missing → config_error. Optional missing → warn."""
    found = {}
    missing = missing_components(printer, required)
    if missing:
        _raise_config(printer, msg.components_required_missing(kind, missing))
    for name in required:
        found[name] = lookup_component(printer, name)
    for name in optional:
        obj = lookup_component(printer, name)
        if obj is None:
            logging.warning("%s", msg.component_optional_missing(kind, name))
        found[name] = obj
    return found


def ensure_feature_components(printer, kind: str, required=(), optional=()) -> dict:
    """Host extra, then declared Klipper extras."""
    if lookup_component(printer, extra_object()) is None:
        _raise_config(printer, msg.feature_requires_host(kind))
    return check_components(printer, kind, required, optional)
