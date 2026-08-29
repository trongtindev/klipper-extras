from klipper_common.constants import (
    CONFIG_OPTION_KEYS,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    LOG_LEVEL_WARNING,
    log_level_enabled,
)
from klipper_common.features import FEATURE_GCODES, FEATURE_KINDS, FEATURE_LOADERS
from klipper_common.features.wipe_nozzle_on_bed import KIND as BED_KIND, OPTION_KEYS as BED_KEYS
from klipper_common.features.wipe_nozzle_on_rubber import (
    KIND as RUBBER_KIND,
    OPTION_KEYS as RUBBER_KEYS,
)


def test_host_config_option_keys():
    assert CONFIG_OPTION_KEYS == frozenset(("log_level",))
    assert "start_x" not in CONFIG_OPTION_KEYS


def test_feature_registry():
    assert FEATURE_KINDS == frozenset((BED_KIND, RUBBER_KIND))
    assert set(FEATURE_LOADERS) == FEATURE_KINDS
    assert FEATURE_GCODES[BED_KIND] == "WIPE_NOZZLE_ON_BED"
    assert FEATURE_GCODES[RUBBER_KIND] == "WIPE_NOZZLE_ON_RUBBER"


def test_feature_option_keys_are_owned_and_not_host():
    assert "start_x" in BED_KEYS
    assert "start_x" in RUBBER_KEYS
    assert "z_hop" in BED_KEYS
    assert "z_hop" in RUBBER_KEYS
    assert "wipe_length" in BED_KEYS
    assert "wipe_length" not in RUBBER_KEYS
    assert "end_x" not in BED_KEYS
    assert "end_y" not in BED_KEYS
    assert "end_x" in RUBBER_KEYS
    assert "end_y" in RUBBER_KEYS
    assert "edge" not in BED_KEYS
    assert "edge" not in RUBBER_KEYS
    assert BED_KEYS.isdisjoint(CONFIG_OPTION_KEYS)
    assert RUBBER_KEYS.isdisjoint(CONFIG_OPTION_KEYS)


def test_log_level_enabled_ladder():
    assert log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_WARNING)
    assert log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_INFO)
    assert not log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_VERBOSE)
    assert not log_level_enabled(LOG_LEVEL_INFO, LOG_LEVEL_DEBUG)
    assert log_level_enabled(LOG_LEVEL_DEBUG, LOG_LEVEL_VERBOSE)
