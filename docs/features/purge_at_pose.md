# Purge at pose

Enabled only by `[klipper_common purge_at_pose]`. Registers **`PURGE_AT_POSE`**. Host `[klipper_common]` is required.

**Purge only** — travels to a fixed XYZ then extrudes **in place** (no XY while purging). Does not wipe or clean. Call [wipe on rubber](wipe_nozzle_on_rubber.md) afterwards if you want to scrape a pad.

Independent of [purge on bed](purge_on_bed.md). Klipper has no purge-bucket pose — do not infer XY from axis max / `safe_z_home`. Set `start_x`, `start_y`, `purge_z` or connect fails.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). Comment template: [`config/sample-purge-at-pose.cfg`](../../config/sample-purge-at-pose.cfg). Owned keys: `features/purge_at_pose/` `OPTION_KEYS`.

## Section

```ini
[klipper_common purge_at_pose]
start_x: 0
start_y: 0
purge_z: 2
```

Use your chute / bucket / park pose, not the numbers above as a universal machine default.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` `purge_z` | float | **required** | mm. Stand-still purge pose. `purge_z` must be `>= 0`. |
| `purge_amount` | float | `10` | mm filament (E). `> 0`. |
| `flow_rate` | float | `12` | mm³/s. `> 0`. E speed from `[extruder] filament_diameter`. |
| `tip_distance` | float | `0` | mm E unretract before purge. `0` skips. |
| `z_hop` | float | `safe_z_home` `z_hop` or `5` | mm. In-place lift before XY travel. Must be `>= 0`. Not used as `travel_z`. |
| `travel_z` | float | `5` | mm. XY travel height (must be `> purge_z`). Profile `5` unless this key is set. |
| `travel_speed` | float | `max_velocity` | mm/s from toolhead / `[printer]`. Profile `200` only if that field is missing. |
| `retract` | float | `0.5` or firmware retraction | mm; `0` skips |
| `retract_speed` | float | `5` or firmware retraction | mm/s |
| `min_nozzle_temp` | float | see heat | Floor (°C). **Required** unless `nozzle_temperature` is set. Order: `[extruder] min_extrude_temp` < `[klipper_common] min_nozzle_temp` < this section. Do not invent `170`. |
| `nozzle_temperature` | float | omitted | If set: `M109` to this value. Else `M109` to `min_nozzle_temp` when current is below it (or to the heater target if that is already ≥ the floor). |
| `fan_speed` | float | `1.0` | 0.0–1.0; restored after purge |
| `fan` | string | `fan` if that object exists, else skip | Missing user-named fan is a config error |
| `before_<action>_gcode` / `after_<action>_gcode` | G-code template | empty | Per-action hooks. See **Actions**. |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` |

No `style`, `purge_length`, `purge_margin`, `along`, or `style_size` on this section.

`[extruder] filament_diameter` is required. E speed is also clamped to `max_extrude_only_velocity` when that field exists. `travel_z > purge_z`. Heat is required: missing floor and `nozzle_temperature` is a config error; a cold nozzle is heated to the floor (or to `nozzle_temperature`).

## Actions

| Action | Work |
|--------|------|
| `heat` | nozzle wait / `M109` |
| `fan` | set fan speed |
| `z_hop` | lift Z in place |
| `travel` | XY at `travel_z` to the pose |
| `lower` | drop to `purge_z` |
| `tip` | unretract `tip_distance` (`0` skips) |
| `purge` | `G1 E{purge_amount}` only |
| `retract` | `G1 E−retract` |
| `lift` | lift to `travel_z` |

No `break` / `recover`. Command wrap: [hook.md](hook.md). `SAVE_GCODE_STATE NAME=PURGE_AT_POSE` after homing; restore in `finally` (`MOVE=1`). Fan restored separately. Retract is not undone.

## G-code

```
PURGE_AT_POSE [PURGE_AMOUNT=<mm>] [PURGE_LENGTH=<mm>]
```

`PURGE_LENGTH` aliases `PURGE_AMOUNT`. Overlay one call; does not write the snapshot. Does not overlay XY.

```gcode
PURGE_AT_POSE
; WIPE_NOZZLE_ON_RUBBER
```

## Status

Host `printer.klipper_common.purge_at_pose`: true when this section is loaded.

Prefix object `printer["klipper_common purge_at_pose"]`: `kind`, `enabled`, `gcode`, `origin_mode`, `start_x`, `start_y`, `purge_z`, `purge_amount`.
