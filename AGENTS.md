# Agent instructions — Klipper Common Plugin

Klipper Python extra (`[klipper_common]`), loaded via `load_config`. Software lives under `plugin/`, `tests/`, `docs/`, `config/`. Runtime is Klipper extras (symlink via `plugin/install.sh`), not PyPI.

This extra is a **host** plus **owned features**. The host is version floor, log levels, status G-codes, installer. Features are enabled by documented `[klipper_common <kind>]` prefix sections (`load_config_prefix`). Do not add undocumented sections or printer-model literals.

Installer / Moonraker behavior follows [klicky-probe-plugin](https://github.com/trongtindev/klicky-probe-plugin).

## Host vs feature ownership (do not stuff features into the host)

- **Host** (`plugin/klipper_common/` root: `__init__.py`, `constants.py`, `defaults.py`, `config_validate.py`, `messages.py`, `klipper_version.py`): no feature option keys, no feature XY/Z/speed defaults, no feature G-code names. `min_nozzle_temp` on `[klipper_common]` is a shared nozzle floor (not geometry); purge reads it. Wipe / form tip do not.
- **Features** live under `plugin/klipper_common/features/<kind>/`. That package owns: `KIND`, `GCODE`, `OPTION_KEYS`, profile defaults, settings resolve, messages, `load_feature`.
- Register a feature only in `features/__init__.py` (`FEATURE_LOADERS` / `FEATURE_GCODES`). Kinds without a command omit `FEATURE_GCODES`. Host `load_config_prefix` dispatches through that map — do not `if kind == …` in host modules.
- Shared algorithms used by *related* features (e.g. wipe path planner, purge styles) go in `features/<family>/` (`wipe_motion/`, `purge_motion/`), **not** in host files. A library is not a feature and has no config section.
- New feature → new package + registry entry + **`docs/features/<kind>.md`** + **`config/sample-<kind>.cfg`**. Never grow host `CONFIG_OPTION_KEYS` or dump feature options into host `docs/configuration.md` / `docs/gcodes.md`.

## Features run independently (no option / pose collision)

- Each prefix section is a **separate Klipper object** with its **own** resolved settings snapshot.
- Bed and rubber (and future features) may be enabled **together**. `start_x` in `[klipper_common wipe_nozzle_on_bed]` is not the rubber pad; rubber coords live only in `[klipper_common wipe_nozzle_on_rubber]`.
- Do not share a mutable settings object across features. Do not read another feature’s keys. G-code state `NAME` is the feature G-code (see **Feature G-code state** below).
- Same option *names* in different sections are fine; they are different namespaces. Do not put feature geometry on `[klipper_common]`.

## Feature G-code state (save / restore)

Any feature command that issues motion or changes G-code mode (G90/G91, F, retract, fan) **must** wrap that work so the printer returns to the pre-command state.

- `SAVE_GCODE_STATE` **after** homing checks, **before** the first mode or motion command. Heat wait is a hooked action: it runs **after** save, inside `try`.
- `RESTORE_GCODE_STATE` in `finally` (success **and** error). Use `MOVE=1` so XYZ return; `MOVE_SPEED` is that feature’s travel speed in **mm/s** (Klipper’s unit — do not multiply by 60).
- `NAME` is the feature G-code (`WIPE_NOZZLE_ON_BED`), never a shared `"wipe"`. Sequential `WIPE_NOZZLE_ON_BED` then `WIPE_NOZZLE_ON_RUBBER` must not restore the wrong snapshot.
- Lift to `travel_z` in absolute mode (`G90`) before `MOVE=1` so a failed wipe at `wipe_z` cannot scrape.
- Fan is **not** in G-code state — snapshot speed before save and restore fan separately.
- Klipper `MOVE=1` does not reverse E; do not unretract on restore.
- Restore failure: log a **warning**. Do not raise from `finally` (that hides the original error). Do not swallow it at `debug` as a silent fallback.
- Host-only commands that do not move (`COMMON_STATUS`, `COMMON_VERSION`) do not save/restore.

## Feature hooks (before / after each action)

Every **action** in an action feature (not only the G-code command) must have before and after hook **call sites**. Empty Klipper G-code template = no-op. Skipped work (retract `0`, no heat, …) skips that action’s hooks. Host-only commands do not.

Two layers. **The feature that owns the action owns that layer’s hook keys, templates, call sites, docs, sample.** Do not import `hook.OPTION_KEYS` into another feature (`debug` / `command_*_gcode` live only on `[klipper_common hook]`). Do not put hook keys on `[klipper_common]`.

- **Common** `[klipper_common hook]` (optional): `command_before_gcode` / `command_after_gcode` / `on_hook_fail` / `debug`. No G-code command. Other extras `lookup_object("klipper_common hook", None)` — do not read that section’s keys.
- **Feature**: `before_<action>_gcode` / `after_<action>_gcode` / `on_hook_fail` on **that** section. Wipe action names live in `wipe_motion` (`WIPE_HOOK_ACTIONS`). Form tip names live in `form_tip` (`FORM_TIP_HOOK_ACTIONS`).

### One implementation — do not copy

| Need | Use this | Do not |
|------|----------|--------|
| before → work → after | `hook/execute.py` `run_hooked_action` / `bind_hooked` (one bind per extra `__init__`) | Duplicate `_hooked` methods; `call_action_hook` before **and** after around work; copy `hook_context` / debug / render into a feature |
| Command wrap | `call_common_hook(printer, "before"\|"after", {"kind": self.kind})` | `lookup_object("klipper_common hook")` then call templates yourself |
| Load templates | `hook/load.py` `load_action_hook_templates` in extra `__init__` | Stuff templates into `WipePathSettings` / `FormTipSettings`; `config.get` then `run_script` later |
| Parse section keys | `hook/load.py` `parse_user_config` (skips `*_gcode` / `on_hook_fail`) | Copy `config_has` + skip-hook-key loops into each feature |
| Feature hook option keys | `hook/policy.py` `hook_option_keys_for_actions(THAT_FEATURE_ACTIONS)` unioned into that feature’s `OPTION_KEYS` | Hand-roll `before_%s_gcode` loops; add `debug` or `command_*_gcode` to a wipe/form_tip section |
| `debug` console log | `[klipper_common hook]` `debug` only (no section → no debug). `call_hook` logs **every** invoke, including empty templates (`(empty)`) | A second debug flag on another section; skip empty templates in the debug log; `print()` / extra `respond_info` at call sites |

New action → add the name to that feature’s `*_HOOK_ACTIONS` tuple, one `self._hooked(...)` call site (`bind_hooked` in `__init__`), docs + sample. Do not add hook option keys by hand.

Load templates like Klipper `[probe] activate_gcode`: `printer.load_object(config, "gcode_macro").load_template(config, option, "")`. Run from a command handler: **render and** `run_script_from_command` in the **same** `try` (`run_hook_template`) so `continue` catches `{ action_raise_error('…') }` (raised during render). Do not `template.render()` then run in a separate `try`. **Never** `run_script()` (gcode mutex).

`on_hook_fail`: `stop` (default) \| `continue` via `config.getchoice` (`load_on_hook_fail`). `stop` lets `printer.command_error` propagate. `continue` catches **only** `command_error` from render **and** nested G-code, logs a warning, proceeds. Never `except Exception` / `except:` around hooks (internal errors shut down the printer). Unknown G-code is **not** a failure in Klipper; users fail a hook with `{ action_raise_error('…') }`.

Call order after homing checks and `SAVE_GCODE_STATE`, still in `try` (not `finally`):

1. Common `command_before_gcode` if the hook object exists (`call_common_hook`)
2. Each feature action that runs: `run_hooked_action` (before → work → after)
3. Common `command_after_gcode` only if step 2 succeeded
4. `finally`: restore fan + G-code state — **no hooks**; do not raise from `finally`

## Settings resolution (do not invert)

1. Parse **only keys present** in that Klipper section. Host: `__init__.py` `_parse_user_config`. Action features with hook keys: `hook/load.py` `parse_user_config`. Do not treat Klipper `config.get(..., default)` as “user set”.
2. For omitted keys: **Klipper field or calc** when the object/field exists. Read via `klipper_fields.py` using **klippy** names only (`toolhead.get_max_velocity()`, `extruder.get_heater().min_extrude_temp`, `filament_area`, `max_e_velocity`, `max_extrude_ratio * filament_area`). Key-in-file: `PrinterConfig.status_raw_config` (`lookup_object("configfile")`). Do not try config-key names as object attributes, and do not fall back through a second API. Hints are read at `klippy:connect`, not guessed. Example: omitted `travel_speed` is `[printer] max_velocity`. Docs: [configuration.md](docs/configuration.md) **Klipper sources**.
3. Else **feature safe default** from that feature’s `constants.py` (named profile values; never printer-model coordinates).
4. A **user-declared** value **overrides** hint and plugin default (set `travel_speed` on that feature section). Empty/missing → hint or default. XY speeds are then capped at `max_velocity`. Do not fill `travel_z` from `z_hop`.

Canonical pick helpers: `resolve.py` (`pick_float`, `pick_speed`). Do not copy `present` / `pick_float` into a feature.

Do **not** invent config keys. Host keys: `CONFIG_OPTION_KEYS`. Each feature: its `OPTION_KEYS`. Docs/sample must be a subset of the matching set.

### No silent fallback

- Do not swap in a second source when the first is missing or unusable (mesh → axis, clamp pose into a box, shrink `margin`, shorten `wipe_length` to fit). That hides the real config and makes debug painful.
- Fail with the **current** value and the **needed** value in the error.
- Documented resolve order (user → hint → profile) is not a fallback: an omitted key follows that order once, in the open.
- **Bed wipe** is a horizontal strip (same Y, back-and-forth on X). User pose keys: `start_x`, `start_y`, `wipe_length`. Computed `end_x` = `start_x` + `wipe_length`, `end_y` = `start_y`. Do not put `end_x`/`end_y` on bed. Do not derive geometry from `bed_mesh` or axis min/max.
- **Rubber** is the only wipe “box”: user `start_x`/`start_y`/`end_x`/`end_y` on the pad. Do not invent that pose from axis / `safe_z_home`.

### No hardcoding

- No machine-specific XY/Z/speed (no Bambu/Voron/… coordinates) in code, tests, or sample as if they were universal.
- Numeric literals used in more than one place in the **same owner** → that owner’s `constants.py`.
- Geometry/speed/temp that Klipper already has → read or derive from those fields; do not duplicate as magic numbers.
- If Klipper has no field (e.g. rubber wiper pose), do **not** invent one from axis max / `safe_z_home`. Safe default or require the user key; then validate.

### Safe defaults

- Profile defaults must be conservative (`wipe_z >= 0`, speeds clamped to `max_velocity`). Use `[extruder] min_extrude_temp` only when that key is present in config; do not invent `170`. When that hint is the heat floor, add `MIN_EXTRUDE_TEMP_HEAT_MARGIN` (5 °C) so PID dips stay above Klipper’s extrude floor (`heat_floor_from_min_extrude_temp` in host `constants.py`). User `min_nozzle_temp` / `nozzle_temperature` are not padded. Wipe / form tip: if absent (and no `min_nozzle_temp` / `nozzle_temperature`), skip heat wait and **warn on the console**; extruder operations (retract, fan) are also skipped. **Purge must heat:** floor from `[extruder] min_extrude_temp` + margin < `[klipper_common] min_nozzle_temp` < the purge section. Missing floor and `nozzle_temperature` is a config error (do not skip). At command, `M109` to `nozzle_temperature` or to the floor when the nozzle is colder (host floor is read from `[klipper_common]` config / `_user`, not only `host.settings` after connect).
- Hints and profiles must not emit negative `wipe_z`. User may still be rejected by validation if unsafe.

## Source of truth

| Concern | Canonical location |
|---------|-------------------|
| Host version, log literals, host option keys, `min_extrude_temp` heat margin | `plugin/klipper_common/constants.py` (`KLIPPER_COMMON_VERSION`, `MIN_EXTRUDE_TEMP_HEAT_MARGIN`) |
| Parse host keys | `__init__.py` `_parse_user_config` |
| Host defaults + `CommonSettings` | `defaults.py` `resolve_settings` |
| Field resolve (user → hint → profile) | `resolve.py` (`pick_float`, `pick_speed`) |
| Live Klipper field reads | `klipper_fields.py` (used by feature hints) |
| Host validation | `config_validate.py` `validate_common_config` |
| Host user/log strings | `messages.py` (`%` formatting only) |
| Feature registry | `features/__init__.py` |
| Prefix dispatch | `__init__.py` `load_config_prefix` |
| Wipe motion library (planner, hints, runner, wipe action names) | `features/wipe_motion/` |
| Bed wipe keys/defaults/G-code | `features/wipe_nozzle_on_bed/` |
| Rubber wipe keys/defaults/G-code | `features/wipe_nozzle_on_rubber/` |
| Purge motion library (planner, styles, hints, runner, purge action names) | `features/purge_motion/` |
| Bed purge keys/defaults/G-code | `features/purge_on_bed/` |
| Pose purge keys/defaults/G-code | `features/purge_at_pose/` |
| Form tip keys/defaults/G-code | `features/form_tip/` |
| Common command hooks (no G-code) | `features/hook/` |
| Hook invoke (render/run, debug, command wrap) | `features/hook/execute.py` (`bind_hooked`, `run_hooked_action`, `call_common_hook`, `call_hook`) |
| Hook load (templates, `parse_user_config`, `on_hook_fail`, `debug`) | `features/hook/load.py` |
| Hook key helper / `on_hook_fail` resolve | `features/hook/policy.py` (`hook_option_keys_for_actions`) |
| Host option reference | `docs/configuration.md` |
| Host G-codes | `docs/gcodes.md` |
| Feature option + G-code reference | `docs/features/<kind>.md` |
| Host comment/uncomment template | `config/sample-klipper-common.cfg` |
| Feature comment/uncomment template | `config/sample-<kind>.cfg` |
| Install / Moonraker | `docs/install.md`, `plugin/install.sh`, `plugin/uninstall.sh`, `plugin/moonraker.snippet.conf` |

## Docs + sample stay in the same change

Any add/remove/rename or behavior/default change of `[klipper_common]` options, prefix kinds, feature options, G-codes, hint/default behavior, installer/Moonraker, or Klipper version floor must update the matching docs (table above). Host docs stay host-only; feature docs stay under `docs/features/`. README sketch only if the user-visible **host** minimal config changes.

## No dead code

When unused code is found, or when logic / options / G-codes / APIs change, **delete the old path in the same change**. Do not leave it beside the new one.

- Drop unused functions, methods, constants, messages, option keys, imports, branches, tests, docs, and sample lines with the behavior they served.
- Do not comment-out, `# TODO remove`, or keep “ignored if present” shims for removed keys.
- A rename or replacement is a delete + add, not a second copy.
- Docs, sample, and tests in the same change (see above). Do not keep examples of options that `OPTION_KEYS` no longer has.

## No temporary patches / workarounds

Do not ship a temporary patch, shim, or workaround to “get unstuck.” Fix the real cause in the same change, or **stop**.

- When writing **new** code or **changing** existing code, if you are blocked (unclear design, conflicting rules, missing Klipper field, tests vs. product intent, two plausible APIs, …), **stop and confirm with the user**. State the blocker and options; wait for a chosen plan. Do not pick a workaround and continue.
- Do not leave `# workaround`, `# HACK`, `# FIXME later`, extra try/except, duplicated paths, or “good enough for now” branches.
- A user-approved design is not a workaround. An unapproved shortcut is.

## Architecture

- **Pure logic** (host `defaults` / `config_validate` / `messages` / `klipper_version` / `constants`; feature `constants` / resolve / validate / messages): **no** Klipper imports. Unit-test without a Klipper tree.
- **`__init__.py`**: host Klipper I/O, `register_command`, config parse, `get_status`, `load_config` / `load_config_prefix` wiring only.
- **`klipper_fields.py`**: live field reads at connect (no klippy import). Duck-types `PrinterConfig.status_raw_config`, `ToolHead.get_max_velocity()`, `PrinterExtruder`.
- **Feature `feature.py` / `wipe_motion/runner.py` / `hints.py` / `hook/feature.py` / `hook/load.py` / `hook/execute.py`**: may import Klipper.
- New modules: module docstring + `from __future__ import annotations`. Relative imports inside the package; tests use `from klipper_common.… import …`.
- Value objects: `@dataclass` / `@dataclass(frozen=True)`.
- Long user/log text → that owner’s `messages.py` as `msg.foo(...)`. No `print()`.
- Keep `Optional[X]` / `typing.List` style (Ruff UP006/007/035/045 ignored). Keep `%` formatting (UP031 ignored).

Ready console banner is **deferred** (`ANNOUNCE_CONSOLE_DELAY`): Moonraker subscribes after READY; emitting in the ready handler never reaches Mainsail.

## Commands

```bash
pip install -e ".[dev]"
ruff check plugin tests
bash tests/test_install_moonraker.sh
bash tests/test_install_extras.sh
pytest tests/ -q
```

- Single test: `pytest tests/test_defaults.py -q` (or `::test_name`).
- Ruff is lint-only here (`pyproject.toml`); `ruff format` is editor-only, not CI.
- `tests/conftest.py` puts `plugin/` on `sys.path` if the editable install is missing.
- Installer extras test **skips as root** (`install.sh` refuses EUID 0). No `systemctl` in tests.
- Source installer as a library: `COMMON_INSTALL_LIB=1 source plugin/install.sh`.

Prefer extending existing tests over ad-hoc scripts.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **klipper_common_plugin** (1306 symbols, 2172 relationships, 53 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/klipper_common_plugin/context` | Codebase overview, check index freshness |
| `gitnexus://repo/klipper_common_plugin/clusters` | All functional areas |
| `gitnexus://repo/klipper_common_plugin/processes` | All execution flows |
| `gitnexus://repo/klipper_common_plugin/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
