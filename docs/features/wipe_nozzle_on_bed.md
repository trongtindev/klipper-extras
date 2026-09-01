# Wipe nozzle on bed

Enabled only by `[klipper_extras wipe_nozzle_on_bed]`. Registers **`WIPE_NOZZLE_ON_BED`**. Host `[klipper_extras]` is required. At connect, an empty `gcode_macro WIPE_NOZZLE_ON_BED` printer object is added so frontends list the command (handler stays on `register_command`).

Independent of [wipe on rubber](wipe_nozzle_on_rubber.md). Motion is a **horizontal** strip (same Y, back-and-forth on X). Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Geometry is not taken from `bed_mesh` or axis min/max.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). When omitted, each key follows [Klipper sources](../configuration.md#klipper-sources). Comment template: [`config/sample-wipe-nozzle-on-bed.cfg`](../../config/sample-wipe-nozzle-on-bed.cfg). Owned keys: `features/wipe_nozzle_on_bed/` `OPTION_KEYS`.

## Section

```ini
[klipper_extras wipe_nozzle_on_bed]
```

Omitted XY → `(50, 50) ↔ (100, 50)` (50 mm along X).

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` | float | `50`, `50` | mm. **No Klipper field.** Start of the strip. |
| `wipe_length` | float | `50` | mm along X. **No Klipper field.** Resolved `end_x` = `start_x` + this; `end_y` = `start_y`. Not a box — `end_x`/`end_y` are rubber-only. |
| `wipe_z` | float | `0.1` | mm. **No Klipper field.** Must be `>= 0`. |
| `z_hop` | float | `[safe_z_home] z_hop` if `> 0`, else `5` | mm. In-place lift. Must be `>= 0`. Not used as `travel_z`. Klipper default hop is `0` (ignored). |
| `travel_z` | float | `5` | mm. **No Klipper field.** XY travel height (must be `> wipe_z`). |
| `wipe_speed` | float | `min(80, [printer] max_velocity)` | mm/s. **No wipe-speed field** in Klipper; `80` is the feature cap. Set this key to override. Then capped at `max_velocity`. |
| `travel_speed` | float | `[printer] max_velocity` | mm/s. Set this key to override. Then capped at `max_velocity`. Profile `200` only if that field is missing. |
| `passes` | int | `1` | **No Klipper field.** `>= 1`. Default is one Y row (back-and-forth on X). |
| `pass_offset` | float | `1` | mm, perpendicular (Y). **No Klipper field.** Used when `passes` `> 1`. |
| `retract` | float | `[firmware_retraction] retract_length`, else `0.5` | mm; `0` skips |
| `retract_speed` | float | `[firmware_retraction] retract_speed`, else `5` | mm/s. Klipper’s section default is `20` if that extra is loaded. |
| `min_nozzle_temp` | float | `[extruder] min_extrude_temp` if that **key** is set, **+ 5 °C** | Do not use Klipper’s implicit `170`. The +5 °C is only for that hint (PID undershoot). User `min_nozzle_temp` / `nozzle_temperature` are not padded. If omitted and no key, skip heat wait (console warning). Retract and fan still run. |
| `nozzle_temperature` | float | omitted | **No Klipper field.** If set: heat and wait. Else wait until current ≥ `min_nozzle_temp` when that floor is known. |
| `fan_speed` | float | `1.0` | **No Klipper field** (`[fan] max_power` is not copied). 0.0–1.0; restored after wipe |
| `fan` | string | `[fan]` if that object exists, else skip | Missing user-named fan is a config error |
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

Command wrap (optional `[klipper_extras hook]`): [hook.md](hook.md). Order after `SAVE_GCODE_STATE`: common before → these actions → common after → restore in `finally` (no hooks). Hooks may move the toolhead; restore still returns XYZ to the pre-command pose.

Unknown commands are not a hook failure. Use `{ action_raise_error('…') }` to stop.

## G-code

`WIPE_NOZZLE_ON_BED` — no parameters (geometry and speeds come from this section).

Errors if `[pause_resume]` reports paused (`is_paused`). Printing (including `PRINT_START` after a Moonraker/SD job start) is allowed.

Call from `PRINT_START` **after XYZ are homed**. Heat the nozzle first, or set `nozzle_temperature` here.

Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Saves G-code state (`SAVE_GCODE_STATE NAME=WIPE_NOZZLE_ON_BED`) after homing checks, before hooks and actions (including heat). Restores in `finally` (`RESTORE_GCODE_STATE NAME=WIPE_NOZZLE_ON_BED MOVE=1`) so coordinate mode, speed override, and XYZ return to the pre-wipe values. Fan is restored separately. Retract is not undone.

```gcode
G28
WIPE_NOZZLE_ON_BED
```

## Status

Host `printer.klipper_extras.wipe_nozzle_on_bed`: true when this section is loaded.

Prefix object `printer["klipper_extras wipe_nozzle_on_bed"]`: `kind`, `enabled`, `gcode`, geometry, `wipe_z`, `passes`.
