# Klipper Extras

A **Klipper Python extra** (`[klipper_extras]`): a small host plus optional, independent features for nozzle wipe, purge, form tip, pause/resume, and command hooks.

Software lives under `plugin/`, `tests/`, `docs/`, `config/`. Runtime is Klipper extras (symlink via `plugin/install.sh`), not PyPI.

Requires **Klipper ≥ v0.13.0** (checked at load).

## What this extra does

Printer start / filament-change sequences usually mix wipe, purge, tip forming, and pause in one giant `printer.cfg` macro. This project splits that into:

1. **Host** — version floor, log levels, status G-codes, installer / Moonraker update manager.
2. **Features** — each enabled only by its own `[klipper_extras <kind>]` section. No section → no G-code. Features can run together; each keeps its own settings (bed wipe `start_x` is not the rubber pad).

Omitted options follow **user → live Klipper field → safe default**. Geometry is not invented from `bed_mesh`, axis min/max, or `safe_z_home`. Feature commands that move save and restore G-code state so the printer returns to the pre-command pose.

## Features

| Section | G-code | What it does |
|---------|--------|----------------|
| `[klipper_extras]` | `EXTRAS_STATUS`, `EXTRAS_VERSION` | Host: version, log level, list of enabled feature commands |
| `[klipper_extras wipe_nozzle_on_bed]` | `WIPE_NOZZLE_ON_BED` | Horizontal wipe strip on the bed (same Y, back-and-forth on X) |
| `[klipper_extras wipe_nozzle_on_rubber]` | `WIPE_NOZZLE_ON_RUBBER` | Wipe on a rubber / brush pad (you set the pad box) |
| `[klipper_extras form_tip]` | `FORM_TIP` | Extruder-only tip forming (no XYZ motion) |
| `[klipper_extras purge_on_bed]` | `PURGE_ON_BED` | Purge pattern on the bed (`line` or `voron`; optional adaptive origin) |
| `[klipper_extras purge_at_pose]` | `PURGE_AT_POSE` | Travel to a chute / bucket pose and purge in place |
| `[klipper_extras pause_resume]` | `PAUSE`, `RESUME`, `CANCEL_PRINT` | Retract, Z-hop, optional park; takes over the names UIs send |
| `[klipper_extras hook]` | *(none)* | Optional wrap: `command_before_gcode` / `command_after_gcode` around feature commands |

Purge does **not** wipe. Call a wipe feature after purge if you want to scrape. Bed wipe and rubber wipe are independent and may both be enabled.

Option reference and samples: [configuration](docs/configuration.md) · [G-codes](docs/gcodes.md) · [wipe on bed](docs/features/wipe_nozzle_on_bed.md) · [wipe on rubber](docs/features/wipe_nozzle_on_rubber.md) · [form tip](docs/features/form_tip.md) · [purge on bed](docs/features/purge_on_bed.md) · [purge at pose](docs/features/purge_at_pose.md) · [pause / resume](docs/features/pause_resume.md) · [hooks](docs/features/hook.md)

## Install

```bash
git clone https://github.com/trongtindev/klipper-extras.git
cd klipper-extras
./plugin/install.sh
```

The installer:

- Symlinks `plugin/klipper_extras` into Klipper’s `klippy/extras/`
- Adds a Moonraker `[update_manager klipper_extras]` block when `moonraker.conf` is found
- Restarts Klipper (and Moonraker if the conf changed)

Uninstall:

```bash
./plugin/uninstall.sh
# equivalent:
./plugin/install.sh -u
```

Then add `[klipper_extras]` to `printer.cfg` (see [`config/sample-klipper-extras.cfg`](config/sample-klipper-extras.cfg)). Enable features with their prefix sections and sample files under [`config/`](config/).

Full path / Moonraker notes: [docs/install.md](docs/install.md).

### Minimal config sketch

```ini
[klipper_extras]
# log_level: info
```

Feature samples: [`config/sample-wipe-nozzle-on-bed.cfg`](config/sample-wipe-nozzle-on-bed.cfg), [`config/sample-wipe-nozzle-on-rubber.cfg`](config/sample-wipe-nozzle-on-rubber.cfg), [`config/sample-form-tip.cfg`](config/sample-form-tip.cfg), [`config/sample-purge-on-bed.cfg`](config/sample-purge-on-bed.cfg), [`config/sample-purge-at-pose.cfg`](config/sample-purge-at-pose.cfg), [`config/sample-pause-resume.cfg`](config/sample-pause-resume.cfg), [`config/sample-hook.cfg`](config/sample-hook.cfg).

After restart:

```gcode
EXTRAS_STATUS
```

## Layout

| Path | Role |
|------|------|
| `plugin/klipper_extras/` | Host extra (`load_config` / `load_config_prefix`) |
| `plugin/klipper_extras/features/<kind>/` | One package per feature |
| `plugin/install.sh` | Symlink into Klipper extras + Moonraker update manager |
| `config/sample-*.cfg` | Comment/uncomment templates for `printer.cfg` |
| `docs/` | Host and per-feature reference |
| `tests/` | Pure-logic unit tests (no Klipper tree required for most of them) |

## Tests (development)

```bash
pip install -e ".[dev]"
ruff check plugin tests
bash tests/test_install_moonraker.sh
bash tests/test_install_extras.sh
pytest tests/ -q
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
