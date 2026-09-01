# Configuration — `[klipper_extras]`

Host section only. Feature options live in that feature’s doc.

Comment/uncomment template: [`config/sample-klipper-extras.cfg`](../config/sample-klipper-extras.cfg).

Requires **Klipper ≥ v0.13.0** (checked at load). Install: [install.md](install.md).

## Resolution

For each option in a section (host or feature), one pass:

1. **User** — key present in that section (always wins)
2. **Klipper hint / calc** — live field at connect when it exists (table below). Hints are read at `klippy:connect`, not guessed.
3. **Safe default** from that section’s owner (`constants.py` — not printer-model coordinates)

Set the key on the **feature** section to override. Empty/missing follows 2 then 3 once. XY speeds are then capped at `[printer] max_velocity`.

## Klipper sources

Mapped to Klipper `klippy` (`toolhead.py`, `kinematics/extruder.py`, `extras/heaters.py`, `extras/firmware_retraction.py`, `extras/safe_z_home.py`, `extras/fan.py`, kinematics `get_status`). Config keys are from [Config_Reference](https://www.klipper3d.org/Config_Reference.html).

| Plugin option | Used by | When omitted | Klipper config | Live object (klippy) |
|---------------|---------|--------------|----------------|----------------------|
| `travel_speed` | wipe, purge, pause_resume | `[printer] max_velocity`; profile `200` only if missing | `[printer] max_velocity` (required) | `toolhead.get_max_velocity()[0]` |
| `wipe_speed` | wipe | feature cap (`80` bed / `50` rubber), then cap at `max_velocity` | `[printer] max_velocity` (cap only) | `toolhead.get_max_velocity()[0]` (cap only) |
| `z_hop` | wipe, purge, pause_resume | `[safe_z_home] z_hop` if `> 0`; else profile `5` | `[safe_z_home] z_hop` (default `0` = no hop) | `safe_z_home.z_hop` |
| `travel_z` | wipe, purge | profile `5` | **none** — do not copy `z_hop` | — |
| `retract` | wipe, purge, pause_resume | `[firmware_retraction] retract_length`; else `0.5` | `[firmware_retraction] retract_length` (default `0`) | `firmware_retraction.retract_length` |
| `retract_speed` | wipe, purge, pause_resume | `[firmware_retraction] retract_speed`; else `5` | `[firmware_retraction] retract_speed` (default `20` if section exists) | `firmware_retraction.retract_speed` |
| `min_nozzle_temp` | wipe, purge, form tip; purge also reads host | `[extruder] min_extrude_temp` **only if that key is in the file** (`PrinterConfig.status_raw_config`) **+ 5 °C** (PID margin); purge then `[klipper_extras] min_nozzle_temp`. User `min_nozzle_temp` / `nozzle_temperature` are not padded | `[extruder] min_extrude_temp` (Klipper default `170` if omitted — **not used**) | `extruder.get_heater().min_extrude_temp` |
| `nozzle_temperature` | wipe, purge, form tip | omitted (no heat-to target) | **none** | — |
| `fan` | wipe, purge, form tip | object name `fan` if `[fan]` is loaded; else skip | `[fan]` | `lookup_object("fan")` |
| `fan_speed` | wipe, purge, form tip | wipe/purge `1.0`; form tip `0` | **none** (`[fan] max_power` is PWM scale, not copied) | — |
| `filament_diameter` | purge (not a section key) | required from Klipper | `[extruder] filament_diameter` (required) | `filament_area` → diameter (`PrinterExtruder` does not store diameter) |
| E-only speed cap | purge bead XY, form tip E speeds | no cap if missing | `[extruder] max_extrude_only_velocity` | `max_e_velocity` |
| bead cross-section | purge | skip check if missing | `[extruder] max_extrude_cross_section` (default `4 * nozzle_diameter^2`) | `max_extrude_ratio * filament_area` |
| axis box | purge (error, no clamp) | skip range check if missing | `[stepper_x]` / `[stepper_y]` `position_min` / `position_max` | `toolhead.get_status()` `axis_minimum` / `axis_maximum` (gcode.Coord `.x` / `.y`) |
| `exclude_object` AABB | purge on bed adaptive origin | command error if no objects | `[exclude_object]` | `exclude_object.get_status()["objects"]` |

No Klipper field (profile or **required** on that feature section): pose/`wipe_z`/`purge_z`/`wipe_length`/`passes`/`pass_offset`/`flow_rate`/`purge_amount`/`style`/`along`/`style_size`/`purge_margin`/`purge_length`/`tip_distance` and form-tip geometry/speeds (named `profile` fills those). Pause `park_x`/`park_y` have no field (omit = no XY). `[printer] max_z_velocity` is not copied; Z hops use `travel_speed` (pause: `z_speed`) and Klipper kinematics still apply `max_z_velocity` on the move.

Do not invent pose from axis max / `safe_z_home` `home_xy_position`.

## Host — `[klipper_extras]`

Required. Common log/status surface.

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `log_level` | string | `info` | `warning` \| `info` \| `verbose` \| `debug`. Gates ready banner. |
| `min_nozzle_temp` | float | omitted | Optional nozzle floor (°C). **No Klipper field on this section.** [Purge](features/purge_on_bed.md) uses this between `[extruder] min_extrude_temp` + 5 °C (only if that key is in the file) and the purge section. Wipe / form tip do not read the host key. |

### `log_level`

| Value | Console / log |
|-------|----------------|
| `warning` | No ready banner. Warnings still emit. |
| `info` | Short `klipper_extras v… ready` line (default). |
| `verbose` | Banner + log_level / gcode list. |
| `debug` | Same ready detail as verbose. |

Unknown values are a config error.

## Features

Enabled by a documented `[klipper_extras <kind>]` prefix. Without the section, that G-code is not registered. Features do not store options on `[klipper_extras]`. Multiple features may be loaded at once; each has its own settings snapshot.

Each feature declares Klipper extras (`REQUIRED_COMPONENTS` / `OPTIONAL_COMPONENTS`). Host `[klipper_extras]` is always required. Missing **required** extras fail at `klippy:connect` (no auto-load, no fallback). Optional extras warn and stay `None`.

| Feature | Doc |
|---------|-----|
| Wipe nozzle on bed | [features/wipe_nozzle_on_bed.md](features/wipe_nozzle_on_bed.md) |
| Wipe nozzle on rubber | [features/wipe_nozzle_on_rubber.md](features/wipe_nozzle_on_rubber.md) |
| Form tip | [features/form_tip.md](features/form_tip.md) |
| Purge on bed | [features/purge_on_bed.md](features/purge_on_bed.md) |
| Purge at pose | [features/purge_at_pose.md](features/purge_at_pose.md) |
| Pause / resume / cancel | [features/pause_resume.md](features/pause_resume.md) (`PAUSE`, `RESUME`, `CANCEL_PRINT`; extras `virtual_sdcard`, `pause_resume`, `respond`) |
| Common command hooks | [features/hook.md](features/hook.md) (no G-code; optional wrap) |

## Status (Moonraker / `printer.klipper_extras`)

| Key | Meaning |
|-----|---------|
| `version` | Plugin version (`KLIPPER_EXTRAS_VERSION`) |
| `klipper_version` | Host `software_version` at connect |
| `log_level` | Resolved `log_level` |
| `min_nozzle_temp` | Host floor, or `null` if omitted |
| *(feature kind)* | `true` when that prefix section is loaded (see the feature doc) |
