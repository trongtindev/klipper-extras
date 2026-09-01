"""User-facing strings for wipe-nozzle-on-rubber."""

from __future__ import annotations

from ...messages import extra_section


def help_wipe_rubber() -> str:
    return "Wipe nozzle on a rubber wiper (requires %s)" % (
        extra_section("wipe_nozzle_on_rubber"),
    )
