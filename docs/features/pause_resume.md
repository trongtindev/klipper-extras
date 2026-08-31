# Pause / resume / cancel

Enabled only by `[klipper_common pause_resume]`. Takes over **`PAUSE`**, **`RESUME`**, and **`CANCEL_PRINT`** (the names Mainsail / Fluidd / KlipperScreen send). Host `[klipper_common]` is required.

Klipper’s `[pause_resume]` extra only pauses the SD job and saves `PAUSE_STATE`. This feature adds retract, Z-hop, optional XY park, cancel cleanup, and Mainsail [macro prompts](https://docs.mainsail.xyz/features/macro-prompts/) via `RESPOND TYPE=command`. It does **not** copy Mainsail/Fluidd Jinja macros.

Resolution (user → Klipper hint → safe default): [configuration.md](../configuration.md). Comment template: [`config/sample-pause-resume.cfg`](../../config/sample-pause-resume.cfg). Owned keys: `features/pause_resume/` `OPTION_KEYS`.

## Required Klipper extras

Declared as `REQUIRED_COMPONENTS`. Missing any at connect is a config error (no auto-load):

| Extra | Why |
|-------|-----|
| `[virtual_sdcard]` | SD pause / resume / cancel |
| `[pause_resume]` | Stock BASE (`cmd_PAUSE` / `cmd_RESUME` / `cmd_CANCEL_PRINT`) |
| `[respond]` | `RESPOND TYPE=command` (web prompts) |

This extra **replaces** `PAUSE`, `RESUME`, and `CANCEL_PRINT` at `klippy:ready` (after `[gcode_macro]` `rename_existing`). Do **not** copy Mainsail/Fluidd Jinja macros. At `klippy:connect` it registers empty printer objects `gcode_macro PAUSE`, `gcode_macro RESUME`, and `gcode_macro CANCEL_PRINT` (`features/ui_macros.py`) so Mainsail / Fluidd list them as macros. Those objects do not handle G-code. If a real `[gcode_macro PAUSE]` (etc.) already exists, that name is skipped (any case).

Mainsail’s **setup checklist** (`gcode_macro pause is not defined in config`) reads **file** sections in `printer.configfile.config`, not printer objects. The Macros panel and the Pause button use the registered commands. That checklist warning does not mean PAUSE is missing. Do not add dummy Jinja macros only to silence it.

Put `[virtual_sdcard]`, `[pause_resume]`, and `[respond]` in `printer.cfg`. `[include mainsail.cfg]` / `fluidd.cfg` is optional for those extras; if included, the three Jinja macros will not run. Missing any required extra is a config error at connect. Leave `CLEAR_PAUSE` on stock Klipper.

## Section

```ini
[klipper_common pause_resume]
```

Omitted `park_x` / `park_y` → **no XY move**. Pause retracts (if the nozzle is hot enough) and lifts Z by `z_hop` in place.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `park_x` `park_y` | float | omitted | mm. **No Klipper field.** Both or neither. Do not invent from axis max. |
| `z_hop` | float | `[safe_z_home] z_hop` if `> 0`, else `5` | mm. In-place lift on pause. `0` skips. Must be `>= 0`. |
| `travel_speed` | float | `[printer] max_velocity` | mm/s. Park XY. Capped at `max_velocity`. |
| `z_speed` | float | same as `travel_speed` | mm/s. Z hop. |
| `retract` | float | `[firmware_retraction] retract_length` else `0.5` | mm. `0` = skip. |
| `retract_speed` | float | fw retract speed else `5` | mm/s. |
| `unretract` | float | same as `retract` | mm on resume. |
| `unretract_speed` | float | same as `retract_speed` | mm/s. |
| `cancel_retract` | float | `5` | mm. `0` = skip. |
| `park_at_cancel` | bool | `False` | XY park before cancel when a park pair exists. |
| `cancel_park_x` `cancel_park_y` | float | pause park pair | Both or neither. |
| `idle_timeout` | float | `0` | Seconds while paused. `0` = do not change Klipper idle_timeout. |
| `restore_temperature` | bool | `True` | `M109` to the target saved at pause if the nozzle cooled. |
| `runout_sensor` | string | omitted | Object name, e.g. `filament_switch_sensor runout`. Blocks `RESUME` if enabled and no filament. |
| `before_pause_gcode` / `after_pause_gcode` | G-code template | empty | Wraps `PAUSE` work (retract / hop / park). [Command templates](https://www.klipper3d.org/Command_Templates.md). |
| `before_resume_gcode` / `after_resume_gcode` | G-code template | empty | Wraps `RESUME` work (heat / unretract). |
| `before_cancel_gcode` / `after_cancel_gcode` | G-code template | empty | Wraps `CANCEL_PRINT` work (optional park, retract, heaters off, fan off). |
| `on_hook_fail` | string | `stop` | `stop` \| `continue` for **this** section’s command hooks. |

## Algorithm

Job state is Klipper `print_stats.state` (loaded with `[virtual_sdcard]`) plus `[pause_resume]` `is_paused`. Each command checks that **before** retract, park, heaters, command hooks, or BASE.

Stock Klipper saves `SAVE_GCODE_STATE NAME=PAUSE_STATE` inside BASE `PAUSE` and restores it on BASE `RESUME` (`MOVE=1`). This feature does **not** save/restore in `finally` on `PAUSE` (the pause spans two commands).

### `PAUSE`

1. Already paused → info, return
2. `print_stats.state` is not `printing` → info, return
3. Snapshot extruder target; optional `SET_IDLE_TIMEOUT`
4. BASE `cmd_PAUSE`
5. Common `command_before_gcode` if `[klipper_common hook]` is loaded
6. `before_pause_gcode` → retract / `z_hop` / park → `after_pause_gcode`
7. Common `command_after_gcode`

Inside step 6: `retract` if hot and `retract` > 0 (cold → warn, skip); `z_hop` if homed Z (`z_park = max(z + z_hop, Z_MIN)` — if that Z exceeds `axis_maximum.z` → error, no silent clamp); `park` only if both park XY are set (config or `X`/`Y`). Empty pause templates still run (no-op). Early return in steps 1–2 skips hooks.

Not homed: BASE still runs; hop/park skipped with a console warning.

### `RESUME`

1. Not paused → info, return
2. Runout (sensor enabled, no filament) → `RESPOND TYPE=error` + prompt; stay paused
3. Common before
4. `before_resume_gcode` → `heat` `M109` if `restore_temperature` and not `can_extrude` but a target was saved; still cold → prompt, **error**, stay paused (`after_resume_gcode` and common after do not run)
5. Else `prompt_end` then `unretract` if hot → `after_resume_gcode`
6. Common after
7. Restore idle_timeout; BASE `cmd_RESUME` (`VELOCITY` or `[pause_resume] recover_velocity`)

Unretract runs **before** BASE so it does not race `virtual_sdcard.do_resume`.

### `CANCEL_PRINT`

1. Not paused and `print_stats.state` is not `printing` / `paused` → info, return
2. `prompt_end`; restore idle_timeout
3. Common before
4. `before_cancel_gcode` → optional park (`park_at_cancel` and XY: cancel pair or pause pair; hop first if `z_hop`) → `cancel_retract` if hot → `TURN_OFF_HEATERS` → `M106 S0` → `after_cancel_gcode`
5. Common after
6. BASE `cmd_CANCEL_PRINT`

## G-code

```
PAUSE [X=<mm> Y=<mm>] [Z_MIN=<mm>]
RESUME [VELOCITY=<mm/s>]
CANCEL_PRINT
```

`X` and `Y` on `PAUSE` are a pair (both or neither), same as config park. `Z_MIN` is a floor for the hop (filament-swap). `VELOCITY` is the speed back to the print pose (Klipper), not park `travel_speed`.

Unknown G-code in hooks is not a failure; use `{ action_raise_error('…') }`.

## Status

Host `printer.klipper_common.pause_resume`: true when this section is loaded.

Prefix object `printer["klipper_common pause_resume"]`: `kind`, `gcodes`, `is_paused`, `park_x`, `park_y`, `z_hop`.
