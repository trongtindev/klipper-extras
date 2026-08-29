#!/usr/bin/env bash
# Uninstall klipper_common (extras symlink + Moonraker update_manager section).
#
# Wrapper around plugin/install.sh -u so uninstall is discoverable as its own
# script. All install.sh flags still apply (-k, -m, -h).
#
# Usage: ./plugin/uninstall.sh [-k KLIPPER_PATH] [-m MOONRAKER_CONF] [-h]
set -euo pipefail
SRCDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SRCDIR}/install.sh" -u "$@"
