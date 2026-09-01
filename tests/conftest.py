"""Shared fixtures for klipper_extras pure-logic tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Prefer editable install (`pip install -e ".[dev]"`). Fallback: put plugin/ on
# sys.path so pytest works without an install (local one-off runs).
try:
    import klipper_extras  # noqa: F401
except ImportError:
    _plugin = Path(__file__).resolve().parents[1] / "plugin"
    if str(_plugin) not in sys.path:
        sys.path.insert(0, str(_plugin))
