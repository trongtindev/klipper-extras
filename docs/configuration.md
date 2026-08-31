# Configuration — `[klipper_common]`

Host section only. Feature options live in that feature’s doc.

Comment/uncomment template: [`config/sample-klipper-common.cfg`](../config/sample-klipper-common.cfg).

Requires **Klipper ≥ v0.13.0** (checked at load). Install: [install.md](install.md).

## Resolution

For each option in a section (host or feature):

1. **User** — key present in that section
2. **Klipper hint** — live field at connect (`max_velocity`, `min_extrude_temp`, firmware retraction, `safe_z_home` z_hop, `fan` object)
3. **Safe default** from that section’s owner (`constants.py` on the host or the feature package — not printer-model coordinates)

A user-declared value always overrides hint and default.

## Host — `[klipper_common]`

Required. Common log/status surface.

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `log_level` | string | `info` | `warning` \| `info` \| `verbose` \| `debug`. Gates ready banner. |
| `min_nozzle_temp` | float | omitted | Optional nozzle floor (°C). [Purge](features/purge_on_bed.md) uses this between `[extruder] min_extrude_temp` and the purge section. Wipe / form tip do not read it. |

### `log_level`

| Value | Console / log |
|-------|----------------|
| `warning` | No ready banner. Warnings still emit. |
| `info` | Short `klipper_common v… ready` line (default). |
| `verbose` | Banner + log_level / gcode list. |
| `debug` | Same ready detail as verbose. |

Unknown values are a config error.

## Features

Enabled by a documented `[klipper_common <kind>]` prefix. Without the section, that G-code is not registered. Features do not store options on `[klipper_common]`. Multiple features may be loaded at once; each has its own settings snapshot.

| Feature | Doc |
|---------|-----|
| Wipe nozzle on bed | [features/wipe_nozzle_on_bed.md](features/wipe_nozzle_on_bed.md) |
| Wipe nozzle on rubber | [features/wipe_nozzle_on_rubber.md](features/wipe_nozzle_on_rubber.md) |
| Form tip | [features/form_tip.md](features/form_tip.md) |
| Purge on bed | [features/purge_on_bed.md](features/purge_on_bed.md) |
| Purge at pose | [features/purge_at_pose.md](features/purge_at_pose.md) |
| Common command hooks | [features/hook.md](features/hook.md) (no G-code; optional wrap) |

## Status (Moonraker / `printer.klipper_common`)

| Key | Meaning |
|-----|---------|
| `version` | Plugin version (`KLIPPER_COMMON_VERSION`) |
| `klipper_version` | Host `software_version` at connect |
| `log_level` | Resolved `log_level` |
| `min_nozzle_temp` | Host floor, or `null` if omitted |
| *(feature kind)* | `true` when that prefix section is loaded (see the feature doc) |
