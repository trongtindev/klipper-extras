# Wipe nozzle on rubber

Enabled only by `[klipper_extras wipe_nozzle_on_rubber]`. Registers **`WIPE_NOZZLE_ON_RUBBER`**. Host `[klipper_extras]` is required. At connect, an empty `gcode_macro WIPE_NOZZLE_ON_RUBBER` printer object is added so frontends list the command (handler stays on `register_command`).

Independent of [wipe on bed](wipe_nozzle_on_bed.md): this section’s coordinates are the **wiper pad**, not the bed strip. Strokes run along the longer axis; with `pass_offset` 0 they are spaced across the shorter axis so both pad edges are used. Both features may be loaded together.

Klipper has no wiper pose — do not infer XY from axis max / `safe_z_home`. Set `start_x`, `start_y`, `end_x`, `end_y` or connect fails.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). When omitted, each key follows [Klipper sources](../configuration.md#klipper-sources). Comment template: [`config/sample-wipe-nozzle-on-rubber.cfg`](../../config/sample-wipe-nozzle-on-rubber.cfg). Owned keys: `features/wipe_nozzle_on_rubber/` `OPTION_KEYS`. Pad `start_*`/`end_*` are this feature’s box — not inferred from axis / mesh.

## Section

```ini
[klipper_extras wipe_nozzle_on_rubber]
start_x: 0
start_y: 0
end_x: 40
end_y: 0
```

Use your pad pose, not the numbers above as a universal machine default.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` `end_x` `end_y` | float | **required** | mm. **No Klipper field** (not axis max / `safe_z_home`). Wiper pad. |
| `wipe_z` | float | `0.0` | mm. **No Klipper field.** Must be `>= 0`. |
| `z_hop` | float | `[safe_z_home] z_hop` if `> 0`, else `5` | mm. In-place lift. Must be `>= 0`. Not used as `travel_z`. Klipper default hop is `0` (ignored). |
| `travel_z` | float | `5` | mm. **No Klipper field.** XY travel height (must be `> wipe_z`). |
| `wipe_speed` | float | `min(50, [printer] max_velocity)` | mm/s. **No wipe-speed field** in Klipper; `50` is the feature cap. Set this key to override. Then capped at `max_velocity`. |
| `travel_speed` | float | `[printer] max_velocity` | mm/s. Set this key to override. Then capped at `max_velocity`. Profile `200` only if that field is missing. |
| `passes` | int | `2` | **No Klipper field.** `>= 1` |
| `pass_offset` | float | `0` | mm, perpendicular. **No Klipper field.** `0`: space `passes` from start to end on the short axis so a rectangle uses both edges. Non-zero: `start + i × offset` (not clamped to the pad). |
| `retract` | float | `[firmware_retraction] retract_length`, else `0.5` | mm; `0` skips |
| `retract_speed` | float | `[firmware_retraction] retract_speed`, else `5` | mm/s. Klipper’s section default is `20` if that extra is loaded. |
| `min_nozzle_temp` | float | `[extruder] min_extrude_temp` if that **key** is set, **+ 5 °C** | Do not use Klipper’s implicit `170`. The +5 °C is only for that hint (PID undershoot). User `min_nozzle_temp` / `nozzle_temperature` are not padded. If omitted and no key, skip heat wait (console warning). Retract and fan still run. |
| `nozzle_temperature` | float | omitted | **No Klipper field.** If set: heat and wait. Else wait until current ≥ `min_nozzle_temp` when that floor is known. |
| `fan_speed` | float | `1.0` | **No Klipper field.** 0.0–1.0; restored after wipe |
| `fan` | string | `[fan]` if that object exists, else skip | Missing user-named fan is a config error |

Speeds `> 0`. `travel_z > wipe_z`. Negative `wipe_z` is a config error. If both `nozzle_temperature` and `min_nozzle_temp` are set, nozzle temp must be `>= min_nozzle_temp`.

Command wrap (optional `[klipper_extras hook]`): [hook.md](hook.md).

## G-code

`WIPE_NOZZLE_ON_RUBBER` — no parameters (geometry and speeds come from this section).

If `[pause_resume]` reports paused: any of `wipe_z`, `z_hop`, `travel_z` **set on this section** is an error (Z would leave the pause height). With those keys omitted, wipe is XY at the current Z (no hop / lower / lift; restore does not lift to `z_hop`; no heat / retract / fan). That is only safe if current Z already clears the print — this plugin’s `PAUSE` hops; stock Klipper does not. Uncommenting `wipe_z` in the sample blocks pause. Printing (including `PRINT_START`) is allowed.

Call from `PRINT_START` **after XYZ are homed**. Heat the nozzle first, or set `nozzle_temperature` here.

Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Saves G-code state (`SAVE_GCODE_STATE NAME=WIPE_NOZZLE_ON_RUBBER`) after homing checks, before command wrap and work (including heat). Restores in `finally` (`RESTORE_GCODE_STATE NAME=WIPE_NOZZLE_ON_RUBBER MOVE=1`) so coordinate mode, speed override, and XYZ return to the pre-wipe values. Fan is restored separately. Retract is not undone. While paused with Z keys omitted, approach/restore do not change Z, and heat / retract / fan are skipped.

```gcode
G28
WIPE_NOZZLE_ON_RUBBER
```

## Status

Host `printer.klipper_extras.wipe_nozzle_on_rubber`: true when this section is loaded.

Prefix object `printer["klipper_extras wipe_nozzle_on_rubber"]`: `kind`, `enabled`, `gcode`, geometry, `wipe_z`, `passes`.
