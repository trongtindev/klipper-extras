#!/usr/bin/env bash
# Installer extras symlink tests (no systemctl). Skipped when EUID=0 because
# install.sh refuses root (same as klicky-probe-plugin).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "OK: $*"; }

if [[ "${EUID}" -eq 0 ]]; then
  echo "SKIP: extras install test (installer refuses root)"
  exit 0
fi

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

klipper="${work}/klipper"
extras="${klipper}/klippy/extras"
mkdir -p "${extras}"
moon="${work}/moonraker.conf"
cat > "${moon}" <<'EOF'
[server]
host: 0.0.0.0
EOF

"${ROOT}/plugin/install.sh" -k "${klipper}" -m "${moon}" >/dev/null

[[ -L "${extras}/klipper_extras" ]] || fail "expected extras symlink"
dest="$(readlink -f "${extras}/klipper_extras")"
[[ "${dest}" == "$(readlink -f "${ROOT}/plugin/klipper_extras")" ]] || \
  fail "symlink dest mismatch: ${dest}"
grep -q '\[update_manager klipper_extras\]' "${moon}" || fail "moonraker section missing"
grep -q "path: ${ROOT}" "${moon}" || fail "moonraker path not repo root"
pass "install symlink + moonraker"

"${ROOT}/plugin/uninstall.sh" -k "${klipper}" -m "${moon}" >/dev/null

[[ -e "${extras}/klipper_extras" ]] && fail "extras path remained after uninstall"
grep -q '\[update_manager klipper_extras\]' "${moon}" && fail "moonraker section remained"
pass "uninstall removes extras + moonraker"

echo ""
echo "All extras install tests passed."
