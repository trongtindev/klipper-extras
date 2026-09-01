"""User-facing strings for wipe-nozzle-on-bed."""

from __future__ import annotations

from ...messages import extra_section


def help_wipe_bed() -> str:
    return "Wipe nozzle on the bed (requires %s)" % (
        extra_section("wipe_nozzle_on_bed"),
    )
