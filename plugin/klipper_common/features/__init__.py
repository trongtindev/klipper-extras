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
from .hook import (
    KIND as HOOK_KIND,
    load_feature as load_hook,
)
from .purge_at_pose import (
    GCODE as PURGE_POSE_GCODE,
    KIND as PURGE_POSE_KIND,
    load_feature as load_purge_at_pose,
)
from .purge_on_bed import (
    GCODE as PURGE_BED_GCODE,
    KIND as PURGE_BED_KIND,
    load_feature as load_purge_on_bed,
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
    HOOK_KIND: load_hook,
    PURGE_BED_KIND: load_purge_on_bed,
    PURGE_POSE_KIND: load_purge_at_pose,
    RUBBER_KIND: load_wipe_nozzle_on_rubber,
}

# Kinds without a G-code command are omitted (hook is config-only).
FEATURE_GCODES = {
    BED_KIND: BED_GCODE,
    FORM_TIP_KIND: FORM_TIP_GCODE,
    PURGE_BED_KIND: PURGE_BED_GCODE,
    PURGE_POSE_KIND: PURGE_POSE_GCODE,
    RUBBER_KIND: RUBBER_GCODE,
}

FEATURE_KINDS = frozenset(FEATURE_LOADERS)
