# Purge at pose

Enabled only by `[klipper_extras purge_at_pose]`. Registers **`PURGE_AT_POSE`**. Host `[klipper_extras]` is required. At connect, an empty `gcode_macro PURGE_AT_POSE` printer object is added so frontends list the command (handler stays on `register_command`).

**Purge only** — travels to a fixed XYZ then extrudes **in place** (no XY while purging). Call [wipe on rubber](wipe_nozzle_on_rubber.md) afterwards if you want to scrape a pad.

Independent of [purge on bed](purge_on_bed.md). Klipper has no purge-bucket pose — do not infer XY from axis max / `safe_z_home`. Set `start_x`, `start_y`, `purge_z` or connect fails.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). When omitted, each key follows [Klipper sources](../configuration.md#klipper-sources). Comment template: [`config/sample-purge-at-pose.cfg`](../../config/sample-purge-at-pose.cfg). Owned keys: `features/purge_at_pose/` `OPTION_KEYS`.

## Section

```ini
[klipper_extras purge_at_pose]
start_x: 0
start_y: 0
purge_z: 2
```

Use your chute / bucket / park pose, not the numbers above as a universal machine default.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` `purge_z` | float | **required** | mm. **No Klipper pose field.** Stand-still purge pose. `purge_z` must be `>= 0`. |
| `purge_amount` | float | `10` | mm filament (E). **No Klipper field.** `> 0`. |
| `flow_rate` | float | `12` | mm³/s. **No Klipper field.** E speed from `[extruder] filament_diameter` (live `filament_area`). Also capped at `[extruder] max_extrude_only_velocity` (`max_e_velocity`). |
| `tip_distance` | float | `0` | mm E unretract. **No Klipper field.** `0` skips. |
| `z_hop` | float | `[safe_z_home] z_hop` if `> 0`, else `5` | mm. Not used as `travel_z`. Klipper default hop is `0` (ignored). |
| `travel_z` | float | `5` | mm. **No Klipper field.** Must be `> purge_z`. |
| `travel_speed` | float | `[printer] max_velocity` | mm/s. Set this key to override. Then capped at `max_velocity`. Profile `200` only if that field is missing. |
| `retract` | float | `[firmware_retraction] retract_length`, else `0.5` | mm; `0` skips |
| `retract_speed` | float | `[firmware_retraction] retract_speed`, else `5` | mm/s |
| `min_nozzle_temp` | float | see heat | Floor (°C). **Required** unless `nozzle_temperature` is set. Order: `[extruder] min_extrude_temp` (key present only) **+ 5 °C** < `[klipper_extras] min_nozzle_temp` < this section. The +5 °C is only for the extruder hint (PID undershoot). User floors are not padded. Do not invent `170`. |
| `nozzle_temperature` | float | omitted | **No Klipper field.** If set: `M109` to this value. Else `M109` to `min_nozzle_temp` when current is below it (or to the heater target if that is already ≥ the floor). |
| `fan_speed` | float | `1.0` | **No Klipper field.** 0.0–1.0; restored after purge |
| `fan` | string | `[fan]` if that object exists, else skip | Missing user-named fan is a config error |
| `before_<action>_gcode` / `after_<action>_gcode` | G-code template | empty | Per-action hooks. See **Actions**. |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` |

`[extruder] filament_diameter` is required. E speed is also clamped to `max_extrude_only_velocity` when that field exists. `travel_z > purge_z`. Heat is required: missing floor and `nozzle_temperature` is a config error; a cold nozzle is heated to the floor (or to `nozzle_temperature`).

## Actions

| Action | Work |
|--------|------|
| `heat` | nozzle wait / `M109` |
| `fan` | set fan speed |
| `z_hop` | lift Z in place |
| `travel` | XY at `travel_z` to the pose (XY only at current Z while paused) |
| `lower` | drop to `purge_z` (skipped while paused) |
| `tip` | unretract `tip_distance` (`0` skips) |
| `purge` | `G1 E{purge_amount}` only |
| `retract` | `G1 E−retract` |
| `lift` | lift to `travel_z` |

Command wrap: [hook.md](hook.md). `SAVE_GCODE_STATE NAME=PURGE_AT_POSE` after homing; restore in `finally` (`MOVE=1`). Fan restored separately. Retract is not undone. If `[quad_gantry_level]` or `[z_tilt]` is loaded and has not been applied, a console warning is printed and purge continues (does not abort).

If `[pause_resume]` reports paused: XY travel to the pose at the **current Z** (no hop / lower / lift; restore does not lift to `travel_z`). Heat / fan / E (tip, purge, retract) still run. `purge_z` on this section is for non-paused use only. That is only safe if current Z already clears the print — this plugin’s `PAUSE` hops; stock Klipper does not. Printing (including `PRINT_START`) uses hop / `travel_z` / `purge_z` as usual.

## G-code

```
PURGE_AT_POSE [PURGE_AMOUNT=<mm>] [PURGE_LENGTH=<mm>]
```

`PURGE_LENGTH` aliases `PURGE_AMOUNT`. Overlay one call; does not write the snapshot. Does not overlay XY.

```gcode
; QUAD_GANTRY_LEVEL  or  Z_TILT_ADJUST  if that extra is loaded
PURGE_AT_POSE
; WIPE_NOZZLE_ON_RUBBER
```

## Status

Host `printer.klipper_extras.purge_at_pose`: true when this section is loaded.

Prefix object `printer["klipper_extras purge_at_pose"]`: `kind`, `enabled`, `gcode`, `origin_mode`, `start_x`, `start_y`, `purge_z`, `purge_amount`.
