"""User-facing strings for purge-on-bed."""

from __future__ import annotations

from ...messages import extra_section


def help_purge_bed() -> str:
    return "Purge filament on the bed (requires %s)" % (
        extra_section("purge_on_bed"),
    )
