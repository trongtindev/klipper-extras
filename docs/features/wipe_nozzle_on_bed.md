# Wipe nozzle on bed

Enabled only by `[klipper_common wipe_nozzle_on_bed]`. Registers **`WIPE_NOZZLE_ON_BED`**. Host `[klipper_common]` is required.

Independent of [wipe on rubber](wipe_nozzle_on_rubber.md). Motion is a **horizontal** strip (same Y, back-and-forth on X). Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Geometry is not taken from `bed_mesh` or axis min/max.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). Comment template: [`config/sample-wipe-nozzle-on-bed.cfg`](../../config/sample-wipe-nozzle-on-bed.cfg). Owned keys: `features/wipe_nozzle_on_bed/` `OPTION_KEYS`.

## Section

```ini
[klipper_common wipe_nozzle_on_bed]
```

Omitted XY → `(50, 50) ↔ (100, 50)` (50 mm along X).

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` | float | `50`, `50` | mm. Start of the strip. |
| `wipe_length` | float | `50` | mm along X. Resolved `end_x` = `start_x` + this; `end_y` = `start_y`. Not a box — `end_x`/`end_y` are rubber-only. |
| `wipe_z` | float | `0.1` | mm. Must be `>= 0`. |
| `z_hop` | float | `safe_z_home` `z_hop` or `5` | mm. In-place lift before XY travel. Must be `>= 0`. |
| `travel_z` | float | `5` | mm. XY travel height (must be `> wipe_z`). |
| `wipe_speed` | float | `min(80, max_velocity)` | mm/s. `80` is the feature cap; `max_velocity` comes from `[printer]`. |
| `travel_speed` | float | `max_velocity` | mm/s from toolhead / `[printer]`. Profile `200` only if that field is missing. |
| `passes` | int | `4` | `>= 1` |
| `pass_offset` | float | `1` | mm, perpendicular (Y) |
| `retract` | float | `0.5` or firmware retraction | mm; `0` skips |
| `retract_speed` | float | `5` or firmware retraction | mm/s |
| `min_nozzle_temp` | float | `[extruder] min_extrude_temp` if that key is set | If omitted and extruder has no `min_extrude_temp`, skip heat wait (console warning). Retract and fan still run. |
| `nozzle_temperature` | float | omitted | If set: heat and wait. Else wait until current ≥ `min_nozzle_temp` when that floor is known. |
| `fan_speed` | float | `1.0` | 0.0–1.0; restored after wipe |
| `fan` | string | `fan` if that object exists, else skip | Missing user-named fan is a config error |
| `before_<action>_gcode` / `after_<action>_gcode` | G-code template | empty | Per-action hooks. See **Actions** below. [Command templates](https://www.klipper3d.org/Command_Templates.md). |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` for **this** section’s action hooks. |

Speeds `> 0`. `travel_z > wipe_z`. Negative `wipe_z` is a config error. If both `nozzle_temperature` and `min_nozzle_temp` are set, nozzle temp must be `>= min_nozzle_temp`.

## Actions

Every action has `before_<action>_gcode` and `after_<action>_gcode` call sites. Empty template = skip. Skipped work (no heat info, `retract` `0`, no fan) skips that action’s hooks.

| Action | Work |
|--------|------|
| `heat` | nozzle wait / `M109` |
| `retract` | `G1 E−retract` |
| `fan` | set wipe fan speed |
| `z_hop` | lift Z in place |
| `travel` | XY at `travel_z` to start |
| `lower` | drop to `wipe_z` |
| `pass` | **each** wipe pass (Jinja `pass_index`) |
| `lift` | lift to `travel_z` |

Command wrap (optional `[klipper_common hook]`): [hook.md](hook.md). Order after `SAVE_GCODE_STATE`: common before → these actions → common after → restore in `finally` (no hooks). Hooks may move the toolhead; restore still returns XYZ to the pre-command pose.

Unknown commands are not a hook failure. Use `{ action_raise_error('…') }` to stop.

## G-code

`WIPE_NOZZLE_ON_BED` — no parameters (geometry and speeds come from this section).

Call from `PRINT_START` **after XYZ are homed**. Heat the nozzle first, or set `nozzle_temperature` here.

Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Saves G-code state (`SAVE_GCODE_STATE NAME=WIPE_NOZZLE_ON_BED`) after homing checks, before hooks and actions (including heat). Restores in `finally` (`RESTORE_GCODE_STATE NAME=WIPE_NOZZLE_ON_BED MOVE=1`) so coordinate mode, speed override, and XYZ return to the pre-wipe values. Fan is restored separately. Retract is not undone.

```gcode
G28
WIPE_NOZZLE_ON_BED
```

## Status

Host `printer.klipper_common.wipe_nozzle_on_bed`: true when this section is loaded.

Prefix object `printer["klipper_common wipe_nozzle_on_bed"]`: `kind`, `enabled`, `gcode`, geometry, `wipe_z`, `passes`.
