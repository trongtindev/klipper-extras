# Purge on bed

Enabled only by `[klipper_common purge_on_bed]`. Registers **`PURGE_ON_BED`**. Host `[klipper_common]` is required.

**Purge only** — extrudes a pattern on the bed. Does not wipe or clean the nozzle. Call [wipe on bed](wipe_nozzle_on_bed.md) afterwards if you want to scrape.

Independent of [purge at pose](purge_at_pose.md). Styles are KAMP `LINE_PURGE` / `VORON_PURGE` patterns (`style: line` or `voron`). Origin is either a **fixed** user `start_x`/`start_y` or **adaptive** from `exclude_object` (both XY omitted). Geometry is not taken from `bed_mesh` or axis min/max (out of range is an error, not a clamp).

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). Comment template: [`config/sample-purge-on-bed.cfg`](../../config/sample-purge-on-bed.cfg). Owned keys: `features/purge_on_bed/` `OPTION_KEYS`.

## Section

```ini
[klipper_common purge_on_bed]
```

Omitted XY → adaptive (needs `exclude_object` objects at command time). Set both `start_x` and `start_y` for a fixed origin.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `style` | string | `line` | `line` \| `voron` (KAMP builtins). |
| `start_x` `start_y` | float | omitted | mm. **Both** → fixed origin (`line`: start of the strip; `voron`: logo bottom-left). **Both omitted** → adaptive. One only → config error. |
| `purge_length` | float | `purge_amount` | mm XY of the `line` stroke. Error if set with `style: voron` (bbox is `style_size`). |
| `purge_margin` | float | `10` | mm. Adaptive only (AABB min − this). Ignored when XY is fixed. |
| `along` | string | `x` | `line` only. `x` \| `y`. Error if set with `voron`. |
| `style_size` | float | `10` | `voron` only. mm logo size. Error if set with `line`. |
| `purge_amount` | float | `30` | mm filament (E). `> 0`. |
| `flow_rate` | float | `12` | mm³/s. `> 0`. E speed from `[extruder] filament_diameter`. |
| `purge_z` | float | `0.8` | mm. Must be `>= 0`. |
| `tip_distance` | float | `0` | mm E unretract before purge. `0` skips. |
| `z_hop` | float | `safe_z_home` `z_hop` or `5` | mm. In-place lift before XY travel. Must be `>= 0`. Not used as `travel_z`. |
| `travel_z` | float | `5` | mm. XY travel height (must be `> purge_z`). Profile `5` unless this key is set. |
| `travel_speed` | float | `max_velocity` | mm/s from toolhead / `[printer]`. Profile `200` only if that field is missing. |
| `retract` | float | `0.5` or firmware retraction | mm; `0` skips retract/recover |
| `retract_speed` | float | `5` or firmware retraction | mm/s |
| `min_nozzle_temp` | float | see heat | Floor (°C). **Required** unless `nozzle_temperature` is set. Order: `[extruder] min_extrude_temp` < `[klipper_common] min_nozzle_temp` < this section. Do not invent `170`. |
| `nozzle_temperature` | float | omitted | If set: `M109` to this value. Else `M109` to `min_nozzle_temp` when current is below it (or to the heater target if that is already ≥ the floor). |
| `fan_speed` | float | `1.0` | 0.0–1.0; restored after purge |
| `fan` | string | `fan` if that object exists, else skip | Missing user-named fan is a config error |
| `before_<action>_gcode` / `after_<action>_gcode` | G-code template | empty | Per-action hooks. See **Actions**. |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` for **this** section’s action hooks. |

`[extruder] filament_diameter` is required (used to convert `flow_rate` to E speed). Speeds `> 0`. `travel_z > purge_z`. Heat is required: missing floor and `nozzle_temperature` is a config error; a cold nozzle is heated to the floor (or to `nozzle_temperature`). Adaptive with no objects → command error (set XY or load objects). Axis overflow → error with current vs needed (no clamp). Insufficient `max_extrude_cross_section` for the bead → error (no skip).

## Adaptive origin

When XY is omitted, at command time (after homing, before save):

- `line` + `along=x`: `start_y = y_min − purge_margin`, `start_x` centered on AABB with `purge_length`
- `line` + `along=y`: `start_x = x_min − purge_margin`, `start_y` centered on AABB
- `voron`: `(x_min − purge_margin, y_min − purge_margin)`

Does not flip X↔Y. Does not default to `(0, 0)`.

## Actions

| Action | Work |
|--------|------|
| `heat` | nozzle wait / `M109` |
| `fan` | set fan speed |
| `z_hop` | lift Z in place |
| `travel` | XY at `travel_z` |
| `lower` | drop to `purge_z` |
| `tip` | unretract `tip_distance` (`0` skips) |
| `purge` | **each** stroke (Jinja `pass_index`). `line` = 1; `voron` = 3 |
| `retract` | `G1 E−retract` |
| `recover` | unretract between `voron` strokes (`retract` `0` skips) |
| `break` | `line` only: rapid +10 mm along the stroke (string break, not a wipe) |
| `lift` | lift to `travel_z` |

Command wrap (optional `[klipper_common hook]`): [hook.md](hook.md). Order after `SAVE_GCODE_STATE`: common before → these actions → common after → restore in `finally` (no hooks).

## G-code

```
PURGE_ON_BED [PURGE_AMOUNT=<mm>] [PURGE_LENGTH=<mm>]
```

`PURGE_LENGTH` is an alias for `PURGE_AMOUNT` (filament mm). Overlay one call; does not write the snapshot. Does not overlay XY or `style`.

Call from `PRINT_START` **after XYZ are homed**. Saves `SAVE_GCODE_STATE NAME=PURGE_ON_BED` after homing (and adaptive origin), restores in `finally` (`MOVE=1`). Fan restored separately. Retract is not undone.

```gcode
G28
PURGE_ON_BED
; WIPE_NOZZLE_ON_BED
```

## Status

Host `printer.klipper_common.purge_on_bed`: true when this section is loaded.

Prefix object `printer["klipper_common purge_on_bed"]`: `kind`, `enabled`, `gcode`, `origin_mode`, `start_x`, `start_y`, `purge_z`, `purge_amount`, `style`.
