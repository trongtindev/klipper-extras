"""Klipper extra instance for [klipper_common wipe_nozzle_on_rubber]."""

from __future__ import annotations

from ..wipe_motion.runner import WipeRunner
from .constants import SPEC


def load_feature(config) -> WipeRunner:
    return WipeRunner(config, SPEC)
