"""User-facing strings for purge-at-pose."""

from __future__ import annotations

from ...messages import extra_section


def help_purge_pose() -> str:
    return "Purge filament at a fixed pose (requires %s)" % (
        extra_section("purge_at_pose"),
    )
