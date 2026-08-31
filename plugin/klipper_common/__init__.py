# Klipper Common — shared Klipper extra (foundation for other extras)
#
# Copyright (C) 2026 Klipper Common contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Install: copy/symlink this package to klippy/extras/klipper_common/
# Config section: [klipper_common]

from __future__ import annotations

import logging

from . import messages as msg
from .config_validate import validate_common_config
from .constants import (
    ANNOUNCE_CONSOLE_DELAY,
    KLIPPER_COMMON_VERSION,
    LOG_LEVEL_DEFAULT,
    LOG_LEVEL_INFO,
    LOG_LEVEL_VERBOSE,
    log_level_enabled,
    ready_lines_for_log_level,
)
from .defaults import resolve_settings
from .features import FEATURE_KINDS, FEATURE_LOADERS, feature_gcode_names
from .klipper_version import MIN_KLIPPER_VERSION, check_min_klipper_version


def _config_has(config, name):
    """Return True if option is present in this config section."""
    try:
        return config.fileconfig.has_option(config.get_name(), name)
    except Exception:
        return False


class KlipperCommon:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.reactor = self.printer.get_reactor()

        self._user = self._parse_user_config(config)
        self.settings = None
        self._klipper_version = "?"
        self._config_warning_count = 0
        self._pending_ready_console_lines = None

        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

        self.gcode.register_command(
            "COMMON_STATUS",
            self.cmd_COMMON_STATUS,
            desc=msg.help_common_status(),
        )
        self.gcode.register_command(
            "COMMON_VERSION",
            self.cmd_COMMON_VERSION,
            desc=msg.help_common_version(),
        )

    def _parse_user_config(self, config):
        user = {}
        if _config_has(config, "log_level"):
            user["log_level"] = config.get("log_level")
        if _config_has(config, "min_nozzle_temp"):
            user["min_nozzle_temp"] = config.get("min_nozzle_temp")
        return user

    def _handle_connect(self):
        ver = self.printer.get_start_args().get("software_version", "?")
        self._klipper_version = str(ver)
        ver_reason = check_min_klipper_version(ver)
        if ver_reason == "too_old":
            raise self.printer.config_error(
                msg.klipper_version_too_old(found=ver, required=MIN_KLIPPER_VERSION)
            )
        if ver_reason == "unparseable":
            raise self.printer.config_error(
                msg.klipper_version_unparseable(
                    found=ver, required=MIN_KLIPPER_VERSION
                )
            )

        try:
            self.settings = resolve_settings(self._user)
        except ValueError as e:
            raise self.printer.config_error(str(e)) from e

        result = validate_common_config(self.settings)
        self._apply_config_validation(result)

        if self._level_enabled(LOG_LEVEL_VERBOSE):
            logging.info(
                "%s",
                msg.log_config_ok(
                    KLIPPER_COMMON_VERSION,
                    self._klipper_version,
                    self.settings.log_level,
                ),
            )

    def _apply_config_validation(self, result) -> None:
        """Emit connect-time warnings; raise config_error if any hard errors."""
        self._config_warning_count = len(result.warnings)
        for issue in result.warnings:
            logging.warning("%s", issue.message)
        if result.errors:
            raise self.printer.config_error(
                msg.config_validation_failed([e.message for e in result.errors])
            )

    def _handle_ready(self):
        if self.settings is None:
            return
        self._schedule_ready_announce()

    def _ready_announce_parts(self):
        """Return (banner, detail_lines) from resolved settings."""
        s = self.settings
        if s is None:
            return None, []
        return msg.ready_banner(KLIPPER_COMMON_VERSION), msg.ready_detail_lines(
            s.log_level, self._extra_gcodes()
        )

    def _schedule_ready_announce(self) -> None:
        """Log banner now; defer console until Moonraker can receive it."""
        banner, detail = self._ready_announce_parts()
        if banner is None:
            return
        level = self._configured_log_level()
        lines = ready_lines_for_log_level(banner, detail, level)
        if (
            self._config_warning_count
            and log_level_enabled(level, LOG_LEVEL_INFO)
            and lines
        ):
            note = msg.config_warnings_ready_note(self._config_warning_count)
            lines = [lines[0], note, *list(lines[1:])]
        for line in lines:
            logging.info("%s", line)
        if not lines:
            return
        self._pending_ready_console_lines = lines
        wake = self.reactor.monotonic() + ANNOUNCE_CONSOLE_DELAY
        self.reactor.register_timer(self._announce_ready_console_timer, wake)

    def _announce_ready_console_timer(self, eventtime):
        """One-shot: emit deferred ready banner to gcode console."""
        lines = self._pending_ready_console_lines or ()
        self._pending_ready_console_lines = None
        for line in lines:
            try:
                self.gcode.respond_info(line, log=False)
            except Exception:
                logging.debug(
                    "klipper_common: ready console emit failed", exc_info=True
                )
        return self.reactor.NEVER

    def _configured_log_level(self) -> str:
        if self.settings is not None:
            return self.settings.log_level
        return LOG_LEVEL_DEFAULT

    def _level_enabled(self, wanted: str) -> bool:
        return log_level_enabled(self._configured_log_level(), wanted)

    def _prefix_loaded(self, kind: str) -> bool:
        name = "klipper_common %s" % (kind,)
        return self.printer.lookup_object(name, None) is not None

    def _extra_gcodes(self) -> list[str]:
        names = []
        for kind in sorted(FEATURE_KINDS):
            if not self._prefix_loaded(kind):
                continue
            names.extend(feature_gcode_names(kind))
        return names

    def cmd_COMMON_STATUS(self, gcmd):
        level = self._configured_log_level()
        extra = self._extra_gcodes()
        gcmd.respond_info(
            msg.status_report(
                KLIPPER_COMMON_VERSION,
                self._klipper_version,
                level,
                extra if extra else None,
            )
        )

    def cmd_COMMON_VERSION(self, gcmd):
        gcmd.respond_info(msg.version_report(KLIPPER_COMMON_VERSION))

    def get_status(self, eventtime):
        status = {
            "version": KLIPPER_COMMON_VERSION,
            "klipper_version": self._klipper_version,
            "log_level": self._configured_log_level(),
            "min_nozzle_temp": (
                None if self.settings is None else self.settings.min_nozzle_temp
            ),
        }
        for kind in FEATURE_KINDS:
            status[kind] = self._prefix_loaded(kind)
        return status


def load_config(config):
    return KlipperCommon(config)


def load_config_prefix(config):
    parts = config.get_name().split(None, 1)
    kind = parts[1] if len(parts) == 2 else ""
    loader = FEATURE_LOADERS.get(kind)
    if loader is None:
        raise config.error(msg.unknown_feature_prefix(kind or config.get_name()))
    return loader(config)
