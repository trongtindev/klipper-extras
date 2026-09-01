from klipper_extras.constants import (
    CONFIG_OPTION_KEYS,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    LOG_LEVEL_WARNING,
    MIN_EXTRUDE_TEMP_HEAT_MARGIN,
    heat_floor_from_min_extrude_temp,
    log_level_enabled,
)
from klipper_extras.features import FEATURE_GCODES, FEATURE_KINDS, FEATURE_LOADERS
from klipper_extras.features.form_tip import (
    KIND as FORM_TIP_KIND,
    OPTION_KEYS as FORM_TIP_KEYS,
)
from klipper_extras.features.hook import KIND as HOOK_KIND, OPTION_KEYS as HOOK_KEYS
from klipper_extras.features.pause_resume import (
    KIND as PAUSE_KIND,
    OPTION_KEYS as PAUSE_KEYS,
    REQUIRED_COMPONENTS as PAUSE_REQUIRED,
)
from klipper_extras.features.purge_at_pose import (
    KIND as PURGE_POSE_KIND,
    OPTION_KEYS as PURGE_POSE_KEYS,
)
from klipper_extras.features.purge_on_bed import (
    KIND as PURGE_BED_KIND,
    OPTION_KEYS as PURGE_BED_KEYS,
)
from klipper_extras.features.wipe_nozzle_on_bed import KIND as BED_KIND, OPTION_KEYS as BED_KEYS
from klipper_extras.features.wipe_nozzle_on_rubber import (
    KIND as RUBBER_KIND,
    OPTION_KEYS as RUBBER_KEYS,
)


def test_host_config_option_keys():
    assert CONFIG_OPTION_KEYS == frozenset(("log_level", "min_nozzle_temp"))
    assert "start_x" not in CONFIG_OPTION_KEYS


def test_heat_floor_from_min_extrude_temp_adds_margin():
    assert MIN_EXTRUDE_TEMP_HEAT_MARGIN == 5.0
    assert heat_floor_from_min_extrude_temp(None) is None
    assert heat_floor_from_min_extrude_temp(170.0) == 175.0


def test_feature_registry():
    assert FEATURE_KINDS == frozenset(
        (
            BED_KIND,
            FORM_TIP_KIND,
            HOOK_KIND,
            PAUSE_KIND,
            PURGE_BED_KIND,
            PURGE_POSE_KIND,
            RUBBER_KIND,
        )
    )
    assert set(FEATURE_LOADERS) == FEATURE_KINDS
    assert FEATURE_GCODES[BED_KIND] == "WIPE_NOZZLE_ON_BED"
    assert FEATURE_GCODES[FORM_TIP_KIND] == "FORM_TIP"
    assert FEATURE_GCODES[PURGE_BED_KIND] == "PURGE_ON_BED"
    assert FEATURE_GCODES[PURGE_POSE_KIND] == "PURGE_AT_POSE"
    assert FEATURE_GCODES[RUBBER_KIND] == "WIPE_NOZZLE_ON_RUBBER"
    assert FEATURE_GCODES[PAUSE_KIND] == ("PAUSE", "RESUME", "CANCEL_PRINT")
    assert HOOK_KIND not in FEATURE_GCODES
    assert PAUSE_REQUIRED == ("virtual_sdcard", "pause_resume", "respond")


def test_feature_option_keys_are_owned_and_not_host():
    assert "start_x" in BED_KEYS
    assert "start_x" in RUBBER_KEYS
    assert "start_x" not in FORM_TIP_KEYS
    assert "z_hop" in BED_KEYS
    assert "z_hop" in RUBBER_KEYS
    assert "z_hop" not in FORM_TIP_KEYS
    assert "wipe_length" in BED_KEYS
    assert "wipe_length" not in RUBBER_KEYS
    assert "wipe_length" not in FORM_TIP_KEYS
    assert "end_x" not in BED_KEYS
    assert "end_y" not in BED_KEYS
    assert "end_x" in RUBBER_KEYS
    assert "end_y" in RUBBER_KEYS
    assert "edge" not in BED_KEYS
    assert "edge" not in RUBBER_KEYS
    assert "tip_distance" in FORM_TIP_KEYS
    assert "profile" in FORM_TIP_KEYS
    assert "style" in PURGE_BED_KEYS
    assert "purge_length" in PURGE_BED_KEYS
    assert "purge_margin" in PURGE_BED_KEYS
    assert "along" in PURGE_BED_KEYS
    assert "style_size" in PURGE_BED_KEYS
    assert "end_x" not in PURGE_BED_KEYS
    assert "style" not in PURGE_POSE_KEYS
    assert "purge_length" not in PURGE_POSE_KEYS
    assert "purge_margin" not in PURGE_POSE_KEYS
    assert "along" not in PURGE_POSE_KEYS
    assert "style_size" not in PURGE_POSE_KEYS
    assert "start_x" in PURGE_POSE_KEYS
    assert "before_purge_gcode" in PURGE_BED_KEYS
    assert "before_purge_gcode" in PURGE_POSE_KEYS
    host_only = CONFIG_OPTION_KEYS - frozenset(("min_nozzle_temp",))
    assert BED_KEYS.isdisjoint(host_only)
    assert RUBBER_KEYS.isdisjoint(host_only)
    assert FORM_TIP_KEYS.isdisjoint(host_only)
    assert HOOK_KEYS.isdisjoint(CONFIG_OPTION_KEYS)
    assert PAUSE_KEYS.isdisjoint(CONFIG_OPTION_KEYS)
    assert "park_x" in PAUSE_KEYS
    assert "before_pause_gcode" in PAUSE_KEYS
    assert "before_resume_gcode" in PAUSE_KEYS
    assert "before_cancel_gcode" in PAUSE_KEYS
    assert "before_park_gcode" not in PAUSE_KEYS
    assert PURGE_BED_KEYS.isdisjoint(host_only)
    assert PURGE_POSE_KEYS.isdisjoint(host_only)
    assert "min_nozzle_temp" in PURGE_BED_KEYS
    assert "min_nozzle_temp" in PURGE_POSE_KEYS
    assert "before_pass_gcode" not in BED_KEYS
    assert "before_pass_gcode" not in RUBBER_KEYS
    assert "on_hook_fail" not in BED_KEYS
    assert "on_hook_fail" not in RUBBER_KEYS
    assert "before_cool_gcode" in FORM_TIP_KEYS
    assert "command_before_gcode" in HOOK_KEYS
    assert "debug" in HOOK_KEYS


def test_log_level_enabled_ladder():
    assert log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_WARNING)
    assert log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_INFO)
    assert not log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_VERBOSE)
    assert not log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_DEBUG)
    assert log_level_enabled(LOG_LEVEL_DEBUG, LOG_LEVEL_VERBOSE)
