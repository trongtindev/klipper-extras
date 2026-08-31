# Common command hooks

Enabled only by `[klipper_common hook]`. **No G-code command.** Host `[klipper_common]` is required.

Wraps each **action feature command** (wipe, form tip, purge, pause/resume/cancel) as a whole. Per-action hooks (`before_pass_gcode`, …) live on that feature’s section — see [wipe on bed](wipe_nozzle_on_bed.md), [wipe on rubber](wipe_nozzle_on_rubber.md), [form tip](form_tip.md). Pause/resume/cancel hooks are **per command** (`before_pause_gcode`, …) on [pause_resume](pause_resume.md), not per retract/park step.

Templates are Klipper G-code macros ([Command templates](https://www.klipper3d.org/Command_Templates.md)). Loaded like `[probe] activate_gcode` (`gcode_macro.load_template`). Comment template: [`config/sample-hook.cfg`](../../config/sample-hook.cfg). Owned keys: `features/hook/` `OPTION_KEYS`.

## Section

```ini
[klipper_common hook]
```

Omitted templates → no-op.

## Options

| Option | Type | Default | Notes |
|--------|------|---------|--------|
| `command_before_gcode` | G-code template | empty | After `SAVE_GCODE_STATE`, before that feature’s actions. |
| `command_after_gcode` | G-code template | empty | After all feature actions succeeded, still before restore. |
| `on_hook_fail` | string | `stop` | `stop` \| `continue`. Applies only to **this** section’s templates. |
| `debug` | bool | `False` | Requires **this** section. When true, **every** hook invoke logs to the console — including **empty** templates (`… (empty)`). Covers this section **and** feature action hooks. |

Jinja context extras: `kind` (the **action** feature kind, e.g. `wipe_nozzle_on_bed`), `action` = `command`, `hook` = `before` or `after`.

Unknown G-code names are **not** a failure in Klipper (console info only). To fail a hook, use `{ action_raise_error('…') }`.

`on_hook_fail: continue` catches only `command_error` from **template render** (`{ action_raise_error('…') }`) and from nested G-code, logs a warning, and proceeds. Internal errors still shut down the printer.

## Call order

Inside the feature command, after homing checks and `SAVE_GCODE_STATE`:

1. This section’s `command_before_gcode` (if this prefix is loaded)
2. That feature’s per-action hooks and work
3. This section’s `command_after_gcode` (only if step 2 did not raise)
4. `finally`: restore fan + `RESTORE_GCODE_STATE` — **no hooks**

## Status

Host `printer.klipper_common.hook`: true when this section is loaded.

Prefix object `printer["klipper_common hook"]`: `kind`, `enabled`, `on_hook_fail`, `debug`.
