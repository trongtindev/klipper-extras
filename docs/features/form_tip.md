# Form tip

Enabled only by `[klipper_extras form_tip]`. Registers **`FORM_TIP`**. Host `[klipper_extras]` is required. At connect, an empty `gcode_macro FORM_TIP` printer object is added so Mainsail / Fluidd list the command (handler stays on `register_command`).

Independent of [wipe on bed](wipe_nozzle_on_bed.md) and [wipe on rubber](wipe_nozzle_on_rubber.md). Motion is **extruder-only** (no XYZ movement). Geometry is set via `tip_distance` (total retract from nozzle) and `sep_fast_len` (fast retract portion).

Resolution (user → Klipper hint → named profile / safe default): [configuration.md](../configuration.md). When omitted, each key follows [Klipper sources](../configuration.md#klipper-sources). Comment template: [`config/sample-form-tip.cfg`](../../config/sample-form-tip.cfg). Owned keys: `features/form_tip/` `OPTION_KEYS`. Named `profile` fills omitted keys; `fan` / `min_nozzle_temp` still take Klipper hints. E speeds are capped at `[extruder] max_extrude_only_velocity` (live `max_e_velocity`).

## Section

```ini
[klipper_extras form_tip]
```

Omitted `profile` → all fields must be user-set (no safe default). Use `profile: a4t_hgx_lite` for the built-in A4T + HGX Lite profile.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `profile` | string | — | **No Klipper field.** `a4t_hgx_lite` selects built-in profile. Omitting requires all fields below. |
| `tip_distance` | float | `35.1` (profile) | **No Klipper field. Required.** Total retract distance from nozzle in mm. |
| `unloading_speed_start_len` | float | `0` | mm. Initial fast retract before separation. `0` = skip. |
| `unloading_speed_start` | float | `80` | mm/s. Speed for initial fast retract. |
| `ramming_len` | float | `0` | mm. Extrude into nozzle before retract. `0` = skip. |
| `ramming_speed` | float | `30` | mm/s. |
| `sep_fast_len` | float | `6` | mm. Fast separation retract after unloading start. |
| `sep_fast_speed` | float | `70` | mm/s. |
| `sep_slow_speed` | float | `15` | mm/s. Speed for `sep_slow_len` (computed: `tip_distance − unloading_speed_start_len − sep_fast_len`). |
| `cooling_moves` | int | `4` | Number of back-and-forth cooling cycles. `0` = skip. |
| `cool_len` | float | `10` | mm. E-length per cooling move. |
| `cool_speed_slow` | float | `12` | mm/s. Starting speed for cooling ramp. |
| `cool_speed_fast` | float | `45` | mm/s. Ending speed for cooling ramp. |
| `use_skinnydip` | bool | `False` | Enable skinnydip (re-melt to remove stringing). |
| `dip_in` | float | `28` | mm. Reinsertion distance for skinnydip. |
| `dip_in_speed` | float | `25` | mm/s. |
| `dip_out_speed` | float | `60` | mm/s. |
| `pause_melt_ms` | int | `0` | ms. Dwell in melt zone during skinnydip. |
| `pause_cool_ms` | int | `0` | ms. Dwell in cooling zone after skinnydip. |
| `parking_distance` | float | `0` | mm. Final retract after tip forming. `0` = skip. |
| `park_speed` | float | `25` | mm/s. |
| `fan_speed` | float | `0` | **No Klipper field.** 0.0–1.0. Fan assist during cooling. `0` = skip. |
| `fan` | string | `[fan]` if that object exists | Fan object name. |
| `nozzle_temperature` | float | omitted | **No Klipper field.** If set: heat and wait before tip forming. |
| `min_nozzle_temp` | float | `[extruder] min_extrude_temp` if that **key** is set, **+ 5 °C** | Do not use Klipper’s implicit `170`. The +5 °C is only for that hint (PID undershoot). User `min_nozzle_temp` / `nozzle_temperature` are not padded. If omitted and no key, skip heat wait (console warning). |
| `before_<action>_gcode` / `after_<action>_gcode` | G-code template | empty | Per-action hooks. See **Algorithm**. [Command templates](https://www.klipper3d.org/Command_Templates.md). |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` for **this** section’s action hooks. |

Lengths, counts, and E speeds in the table (except `fan` / `min_nozzle_temp`) have **no Klipper field**; named `profile` or user keys only. E speeds are then capped at `[extruder] max_extrude_only_velocity`.

`sep_fast_len + unloading_speed_start_len` must be `<= tip_distance`. All speeds > 0. All lengths >= 0. `fan_speed` 0.0–1.0. `cooling_moves >= 0`. `cool_len > 0` when `cooling_moves > 0`. `dip_in > 0` when `use_skinnydip`.

## Algorithm

All speeds are mm/s. Emitted as `F = speed × 60`. Relative extrusion (`M83`) after save.

Each numbered step is an action with `before_<action>_gcode` / `after_<action>_gcode`. Skipped work skips that action’s hooks. `cool` runs **per** cooling pair (`pass_index`). Optional command wrap: [hook.md](hook.md).

1. **`heat`** — `M109` if `nozzle_temperature` set, else `M109` to target if below `min_nozzle_temp`
2. **`unload_start`** — `G1 E−unloading_speed_start_len` (if > 0)
3. **`sep_fast`** — `G1 E−sep_fast_len`
4. **`sep_slow`** — `G1 E−sep_slow_len` (computed, if > 0)
5. **`ramming`** — `G1 E+ramming_len` (if > 0)
6. **`fan`** — `M106` / `SET_FAN_SPEED` (if `fan_speed > 0`, before cooling)
7. **`cool`** — linear speed ramp from `cool_speed_slow` to `cool_speed_fast` across `cooling_moves` pairs
8. **`skinnydip`** — `E+dip_in` → `G4` → `E−dip_in` → `G4` (if `use_skinnydip`)
9. **`parking`** — `G1 E−|parking_distance|` (if != 0)

Fan restored + `RESTORE_GCODE_STATE NAME=FORM_TIP` in `finally` (no hooks). Unknown commands are not a hook failure; use `{ action_raise_error('…') }`.

## G-code

```
FORM_TIP [PARAM=VALUE ...]
```

All option keys can be overridden per-call via UPPER_SNAKE_CASE G-code params. Common aliases:

| Alias | Maps to |
|-------|---------|
| `NOZZLE_TEMP` | `nozzle_temperature` |
| `MIN_NOZZLE` | `min_nozzle_temp` |
| `UNLOAD_START_LEN` | `unloading_speed_start_len` |
| `UNLOAD_START` | `unloading_speed_start` |
| `SEP_FAST` | `sep_fast_len` |
| `COOL` | `cool_len` |
| `FAN` | `fan` |

```gcode
FORM_TIP NOZZLE_TEMP=220 COOLING_MOVES=6
FORM_TIP UNLOAD_START=100 TIP_DISTANCE=40
```

Saves G-code state (`SAVE_GCODE_STATE NAME=FORM_TIP`) after homing checks, before hooks and actions (including heat). Restores in `finally` (`RESTORE_GCODE_STATE NAME=FORM_TIP`) so coordinate mode and speed override return to pre-command values. Fan is restored separately.

## Status

Host `printer.klipper_extras.form_tip`: true when this section is loaded.

Prefix object `printer["klipper_extras form_tip"]`: `kind`, `enabled`, `gcode`, `profile`, `tip_distance`, `sep_fast_len`, `sep_slow_len`, `cooling_moves`, `use_skinnydip`.