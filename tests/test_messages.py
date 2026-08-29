from klipper_common.constants import (
    KLIPPER_COMMON_VERSION,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    LOG_LEVEL_WARNING,
    ready_lines_for_log_level,
)
from klipper_common.klipper_version import MIN_KLIPPER_VERSION
from klipper_common.messages import (
    feature_requires_host,
    klipper_version_too_old,
    ready_banner,
    ready_detail_lines,
    status_report,
    unknown_feature_prefix,
    version_report,
)


def test_ready_banner_contains_version():
    line = ready_banner(KLIPPER_COMMON_VERSION)
    assert KLIPPER_COMMON_VERSION in line
    assert "klipper_common" in line


def test_ready_lines_warning_empty():
    banner = ready_banner()
    detail = ready_detail_lines("info")
    assert ready_lines_for_log_level(banner, detail, LOG_LEVEL_WARNING) == []


def test_ready_lines_info_banner_only():
    banner = ready_banner()
    detail = ready_detail_lines("info")
    lines = ready_lines_for_log_level(banner, detail, LOG_LEVEL_INFO)
    assert lines == [banner]


def test_ready_lines_verbose_includes_detail():
    banner = ready_banner()
    detail = ready_detail_lines("verbose")
    lines = ready_lines_for_log_level(banner, detail, LOG_LEVEL_VERBOSE)
    assert lines[0] == banner
    assert lines[1:] == detail


def test_status_and_version_strings():
    assert "0.1.0" in version_report("0.1.0")
    text = status_report("0.1.0", "v0.13.0", "info")
    assert "0.1.0" in text
    assert "v0.13.0" in text
    assert "info" in text


def test_klipper_too_old_mentions_floor():
    text = klipper_version_too_old("v0.12.0", MIN_KLIPPER_VERSION)
    assert "0.13.0" in text
    assert "v0.12.0" in text


def test_feature_host_messages():
    assert "foo" in unknown_feature_prefix("foo")
    assert "[klipper_common]" in feature_requires_host("wipe_nozzle_on_bed")
