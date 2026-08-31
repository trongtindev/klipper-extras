# Klipper Common Plugin

Klipper **Python extra** (`[klipper_common]`) — shared host for extras (version floor, log levels, status G-codes, optional wipe-nozzle features, Moonraker-aware installer).

Installer layout follows [klicky-probe-plugin](https://github.com/trongtindev/klicky-probe-plugin).

## Software

The extra lives under [`plugin/klipper_common/`](plugin/klipper_common).

- Requires **Klipper ≥ v0.13.0** (checked at load)
- Host section: `[klipper_common]`
- Features (optional prefix sections): see [wipe on bed](docs/features/wipe_nozzle_on_bed.md), [wipe on rubber](docs/features/wipe_nozzle_on_rubber.md), [form tip](docs/features/form_tip.md), [purge on bed](docs/features/purge_on_bed.md), [purge at pose](docs/features/purge_at_pose.md), [command hooks](docs/features/hook.md)
- G-codes: **`COMMON_STATUS`**, **`COMMON_VERSION`**; feature commands only when that section is present
- Pure-logic unit tests (`pytest`)

### Install

```bash
git clone https://github.com/trongtindev/klipper_common_plugin.git
cd klipper_common_plugin
./plugin/install.sh
```

Registers the plugin in Klipper extras and adds a Moonraker update-manager section when `moonraker.conf` is found.

Uninstall:

```bash
./plugin/uninstall.sh
# equivalent:
./plugin/install.sh -u
```

Then add `[klipper_common]` to `printer.cfg` (see [`config/sample-klipper-common.cfg`](config/sample-klipper-common.cfg)).

**Docs:** [Install](docs/install.md) · [Configuration](docs/configuration.md) · [G-codes](docs/gcodes.md) · [Wipe on bed](docs/features/wipe_nozzle_on_bed.md) · [Wipe on rubber](docs/features/wipe_nozzle_on_rubber.md) · [Form tip](docs/features/form_tip.md) · [Purge on bed](docs/features/purge_on_bed.md) · [Purge at pose](docs/features/purge_at_pose.md) · [Hooks](docs/features/hook.md)

### Tests

```bash
pip install -e ".[dev]"
ruff check plugin tests
bash tests/test_install_moonraker.sh
bash tests/test_install_extras.sh
pytest tests/ -q
```

### Minimal config sketch

```ini
[klipper_common]
# log_level: info
```

Feature samples: [`config/sample-wipe-nozzle-on-bed.cfg`](config/sample-wipe-nozzle-on-bed.cfg), [`config/sample-wipe-nozzle-on-rubber.cfg`](config/sample-wipe-nozzle-on-rubber.cfg), [`config/sample-form-tip.cfg`](config/sample-form-tip.cfg), [`config/sample-hook.cfg`](config/sample-hook.cfg).

Verify after restart:

```gcode
COMMON_STATUS
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
