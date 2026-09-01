# Install Klipper Extras

**Docs:** [Configuration](configuration.md) · [G-codes](gcodes.md) · [Wipe on bed](features/wipe_nozzle_on_bed.md) · [Wipe on rubber](features/wipe_nozzle_on_rubber.md) · [Form tip](features/form_tip.md)

## Requirements

- **Klipper ≥ v0.13.0** — checked at load
- Moonraker optional (for update manager)

## Quick install

```bash
cd ~
git clone https://github.com/trongtindev/klipper-extras.git
cd klipper-extras
./plugin/install.sh
```

The install script:

1. Symlinks `plugin/klipper_extras` into `$KLIPPER_PATH/klippy/extras/klipper_extras` (default `~/klipper`)
2. Registers `[update_manager klipper_extras]` in `moonraker.conf` when found. A section is **managed** only when the installer marker comment sits immediately above it (blank lines allowed). Managed sections get path/origin rewritten to the current clone; sections without that adjacent marker are treated as hand-edited and left alone
3. Restarts Klipper when the service is active; restarts Moonraker only when the conf was just modified

Non-default paths:

```bash
export KLIPPER_PATH=/home/pi/klipper
./plugin/install.sh
# or:
./plugin/install.sh -k /home/pi/klipper
./plugin/install.sh /home/pi/klipper

# Custom moonraker.conf:
./plugin/install.sh -m ~/printer_data/config/moonraker.conf
```

### Installer flags

```text
Usage: install.sh [-k KLIPPER_PATH] [-m MOONRAKER_CONF] [-u] [-h] [KLIPPER_PATH]

  -k PATH   Klipper root (default: $KLIPPER_PATH or ~/klipper)
  -m PATH   moonraker.conf path (default: auto-detect)
  -u        Uninstall (extras link + Moonraker update_manager section)
  -h        Help
```

Moonraker conf is searched in order: `$MOONRAKER_CONF` / `-m`, then:

- `~/printer_data/config/moonraker.conf`
- `~/klipper_config/moonraker.conf`
- `~/moonraker.conf`

If no conf is found, install still succeeds; add the update block manually (below).

## printer.cfg

Add a `[klipper_extras]` section (see [configuration.md](configuration.md) and `config/sample-klipper-extras.cfg`):

```ini
[include sample-klipper-extras.cfg]
# or paste [klipper_extras] directly
```

Optional features: [wipe on bed](features/wipe_nozzle_on_bed.md) (`config/sample-wipe-nozzle-on-bed.cfg`), [wipe on rubber](features/wipe_nozzle_on_rubber.md) (`config/sample-wipe-nozzle-on-rubber.cfg`).

## Moonraker update manager

`./plugin/install.sh` adds this automatically when it finds `moonraker.conf`.

Manual fallback — copy the block from `plugin/moonraker.snippet.conf` into `moonraker.conf`, adjusting `path` and `origin` to your clone, then restart Moonraker.

## Uninstall

```bash
./plugin/uninstall.sh
# equivalent:
./plugin/install.sh -u
# optional path overrides:
./plugin/uninstall.sh -k /path/to/klipper -m /path/to/moonraker.conf
```

This removes:

- `$KLIPPER_PATH/klippy/extras/klipper_extras` (symlink or copy)
- `[update_manager klipper_extras]` from `moonraker.conf` (when present)

Then remove `[klipper_extras]` and any `[klipper_extras …]` feature sections from `printer.cfg` and restart if services were not restarted.

```bash
# manual fallback if needed:
rm -rf ~/klipper/klippy/extras/klipper_extras
sudo systemctl restart klipper
```

## Development tests

```bash
pip install -e ".[dev]"
ruff check plugin tests
bash tests/test_install_moonraker.sh
bash tests/test_install_extras.sh
pytest tests/ -q
```
