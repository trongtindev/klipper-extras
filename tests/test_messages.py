from klipper_extras.constants import (
    KLIPPER_EXTRAS_VERSION,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    LOG_LEVEL_WARNING,
    ready_lines_for_log_level,
)
from klipper_extras.klipper_version import MIN_KLIPPER_VERSION
from klipper_extras.messages import (
    components_required_missing,
    extra_section,
    feature_requires_host,
    klipper_version_too_old,
    line,
    pose_required,
    ready_banner,
    ready_detail_lines,
    status_report,
    unknown_feature_prefix,
    version_report,
)


def test_ready_banner_contains_version():
    line = ready_banner(KLIPPER_EXTRAS_VERSION)
    assert KLIPPER_EXTRAS_VERSION in line
    assert "klipper_extras" in line


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
    assert "[klipper_extras]" in feature_requires_host("wipe_nozzle_on_bed")
    missing = components_required_missing("pause_resume", ["respond"])
    assert "respond" in missing
    assert "pause_resume" in missing


def test_line_and_pose_required():
    assert line("hello") == "klipper_extras: hello"
    assert line("%s must be > 0", "wipe_speed") == "klipper_extras: wipe_speed must be > 0"
    assert extra_section() == "[klipper_extras]"
    assert extra_section("hook") == "[klipper_extras hook]"
    text = pose_required("purge_at_pose", "start_x, start_y, purge_z", "purge pose")
    assert "[purge_at_pose]" in text
    assert "start_x, start_y, purge_z" in text
    assert "purge pose" in text
    assert text.startswith("klipper_extras:")
