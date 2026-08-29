# Wipe nozzle on rubber

Enabled only by `[klipper_common wipe_nozzle_on_rubber]`. Registers **`WIPE_NOZZLE_ON_RUBBER`**. Host `[klipper_common]` is required.

Independent of [wipe on bed](wipe_nozzle_on_bed.md): this section’s coordinates are the **wiper pad**, not the bed strip. Strokes run along the longer axis; with `pass_offset` 0 they are spaced across the shorter axis so both pad edges are used. Both features may be loaded together.

Klipper has no wiper pose — do not infer XY from axis max / `safe_z_home`. Set `start_x`, `start_y`, `end_x`, `end_y` or connect fails.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). Comment template: [`config/sample-wipe-nozzle-on-rubber.cfg`](../../config/sample-wipe-nozzle-on-rubber.cfg). Owned keys: `features/wipe_nozzle_on_rubber/` `OPTION_KEYS`. Pad `start_*`/`end_*` are this feature’s box — not inferred from axis / mesh.

## Section

```ini
[klipper_common wipe_nozzle_on_rubber]
start_x: 0
start_y: 0
end_x: 40
end_y: 0
```

Use your pad pose, not the numbers above as a universal machine default.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `start_x` `start_y` `end_x` `end_y` | float | **required** | mm. Wiper pad. |
| `wipe_z` | float | `0.0` | mm. Must be `>= 0`. |
| `z_hop` | float | `safe_z_home` `z_hop` or `5` | mm. In-place lift before XY travel. Must be `>= 0`. |
| `travel_z` | float | `5` | mm. XY travel height (must be `> wipe_z`). |
| `wipe_speed` | float | `min(50, max_velocity)` | mm/s. `50` is the feature cap; `max_velocity` comes from `[printer]`. |
| `travel_speed` | float | `max_velocity` | mm/s from toolhead / `[printer]`. Fallback `200` only if that field is missing. |
| `passes` | int | `4` | `>= 1` |
| `pass_offset` | float | `0` | mm, perpendicular to the wipe axis. `0`: space `passes` from start to end on the short axis so a rectangle uses both edges. Non-zero: `start + i × offset` (not clamped to the pad). |
| `retract` | float | `0.5` or firmware retraction | mm; `0` skips |
| `retract_speed` | float | `5` or firmware retraction | mm/s |
| `min_nozzle_temp` | float | `[extruder] min_extrude_temp` if that key is set | If omitted and extruder has no `min_extrude_temp`, skip heat wait (console warning). Retract and fan still run. |
| `nozzle_temperature` | float | omitted | If set: heat and wait. Else wait until current ≥ `min_nozzle_temp` when that floor is known. |
| `fan_speed` | float | `1.0` | 0.0–1.0; restored after wipe |
| `fan` | string | `fan` if that object exists, else skip | Missing user-named fan is a config error |

Speeds `> 0`. `travel_z > wipe_z`. Negative `wipe_z` is a config error. If both `nozzle_temperature` and `min_nozzle_temp` are set, nozzle temp must be `>= min_nozzle_temp`.

## G-code

`WIPE_NOZZLE_ON_RUBBER` — no parameters (geometry and speeds come from this section).

Call from `PRINT_START` **after XYZ are homed**. Heat the nozzle first, or set `nozzle_temperature` here.

Approach lifts to `travel_z` in place, then moves XY, then drops to `wipe_z`. Saves G-code state (`SAVE_GCODE_STATE NAME=WIPE_NOZZLE_ON_RUBBER`) before motion and restores it afterwards (`RESTORE_GCODE_STATE NAME=WIPE_NOZZLE_ON_RUBBER MOVE=1`) so coordinate mode, speed override, and XYZ return to the pre-wipe values. Fan is restored separately. Retract is not undone.

```gcode
G28
WIPE_NOZZLE_ON_RUBBER
```

## Status

Host `printer.klipper_common.wipe_nozzle_on_rubber`: true when this section is loaded.

Prefix object `printer["klipper_common wipe_nozzle_on_rubber"]`: `kind`, `enabled`, `gcode`, geometry, `wipe_z`, `passes`.
