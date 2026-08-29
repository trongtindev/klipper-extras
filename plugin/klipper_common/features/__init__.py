"""Feature registry. Host dispatches `[klipper_common <kind>]` here only.

Each feature package owns its option keys, defaults, settings, G-code, and
messages. Do not put feature literals in host `constants.py`.
"""

from __future__ import annotations

from .form_tip import (
    GCODE as FORM_TIP_GCODE,
    KIND as FORM_TIP_KIND,
    load_feature as load_form_tip,
)
from .wipe_nozzle_on_bed import (
    GCODE as BED_GCODE,
    KIND as BED_KIND,
    load_feature as load_wipe_nozzle_on_bed,
)
from .wipe_nozzle_on_rubber import (
    GCODE as RUBBER_GCODE,
    KIND as RUBBER_KIND,
    load_feature as load_wipe_nozzle_on_rubber,
)

# kind → loader. Add new features here; do not branch inside host modules.
FEATURE_LOADERS = {
    BED_KIND: load_wipe_nozzle_on_bed,
    FORM_TIP_KIND: load_form_tip,
    RUBBER_KIND: load_wipe_nozzle_on_rubber,
}

FEATURE_GCODES = {
    BED_KIND: BED_GCODE,
    FORM_TIP_KIND: FORM_TIP_GCODE,
    RUBBER_KIND: RUBBER_GCODE,
}

FEATURE_KINDS = frozenset(FEATURE_LOADERS)
