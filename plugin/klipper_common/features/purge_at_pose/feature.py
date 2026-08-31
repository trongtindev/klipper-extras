"""Klipper extra instance for [klipper_common purge_at_pose]."""

from __future__ import annotations

from ..purge_motion.runner import PurgeRunner
from .constants import SPEC


def load_feature(config) -> PurgeRunner:
    return PurgeRunner(config, SPEC)
