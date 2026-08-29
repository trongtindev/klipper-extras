# Agent instructions — Klipper Common Plugin

Klipper Python extra (`[klipper_common]`), loaded via `load_config`. Software lives under `plugin/`, `tests/`, `docs/`, `config/`. Runtime is Klipper extras (symlink via `plugin/install.sh`), not PyPI.

This extra is a **host** plus **owned features**. The host is version floor, log levels, status G-codes, installer. Features are enabled by documented `[klipper_common <kind>]` prefix sections (`load_config_prefix`). Do not add undocumented sections or printer-model literals.

Installer / Moonraker behavior follows [klicky-probe-plugin](https://github.com/trongtindev/klicky-probe-plugin).

## Host vs feature ownership (do not stuff features into the host)

- **Host** (`plugin/klipper_common/` root: `__init__.py`, `constants.py`, `defaults.py`, `config_validate.py`, `messages.py`, `klipper_version.py`): no feature option keys, no feature XY/Z/speed defaults, no feature G-code names.
- **Features** live under `plugin/klipper_common/features/<kind>/`. That package owns: `KIND`, `GCODE`, `OPTION_KEYS`, profile defaults, settings resolve, messages, `load_feature`.
- Register a feature only in `features/__init__.py` (`FEATURE_LOADERS` / `FEATURE_GCODES`). Host `load_config_prefix` dispatches through that map — do not `if kind == …` in host modules.
- Shared algorithms used by *related* features (e.g. wipe path planner) go in `features/<family>/` (today `features/wipe_motion/`), **not** in host files. A library is not a feature and has no config section.
- New feature → new package + registry entry + **`docs/features/<kind>.md`** + **`config/sample-<kind>.cfg`**. Never grow host `CONFIG_OPTION_KEYS` or dump feature options into host `docs/configuration.md` / `docs/gcodes.md`.

## Features run independently (no option / pose collision)

- Each prefix section is a **separate Klipper object** with its **own** resolved settings snapshot.
- Bed and rubber (and future features) may be enabled **together**. `start_x` in `[klipper_common wipe_nozzle_on_bed]` is not the rubber pad; rubber coords live only in `[klipper_common wipe_nozzle_on_rubber]`.
- Do not share a mutable settings object across features. Do not read another feature’s keys. G-code state `NAME` is the feature G-code (see **Feature G-code state** below).
- Same option *names* in different sections are fine; they are different namespaces. Do not put feature geometry on `[klipper_common]`.

## Feature G-code state (save / restore)

Any feature command that issues motion or changes G-code mode (G90/G91, F, retract, fan) **must** wrap that work so the printer returns to the pre-command state.

- `SAVE_GCODE_STATE` **after** homing / temperature checks, **before** the first mode or motion command.
- `RESTORE_GCODE_STATE` in `finally` (success **and** error). Use `MOVE=1` so XYZ return; `MOVE_SPEED` is that feature’s travel speed in **mm/s** (Klipper’s unit — do not multiply by 60).
- `NAME` is the feature G-code (`WIPE_NOZZLE_ON_BED`), never a shared `"wipe"`. Sequential `WIPE_NOZZLE_ON_BED` then `WIPE_NOZZLE_ON_RUBBER` must not restore the wrong snapshot.
- Lift to `travel_z` in absolute mode (`G90`) before `MOVE=1` so a failed wipe at `wipe_z` cannot scrape.
- Fan is **not** in G-code state — snapshot speed before save and restore fan separately.
- Klipper `MOVE=1` does not reverse E; do not unretract on restore.
- Restore failure: log a **warning**. Do not raise from `finally` (that hides the original error). Do not swallow it at `debug` as a silent fallback.
- Host-only commands that do not move (`COMMON_STATUS`, `COMMON_VERSION`) do not save/restore.

## Settings resolution (do not invert)

1. Parse **only keys present** in that Klipper section (`_config_has`). Do not treat Klipper `config.get(..., default)` as “user set”.
2. For omitted keys: **Klipper field or calc** when the object/field exists (`max_velocity`, `min_extrude_temp`, `firmware_retraction`, `safe_z_home` z_hop, `fan` object, …). Hints are read at `klippy:connect`, not guessed.
3. Else **feature safe default** from that feature’s `constants.py` (named profile values; never printer-model coordinates).
4. A **user-declared** value **overrides** hint and plugin default. Empty/missing → hint or default.

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

- Profile defaults must be conservative (`wipe_z >= 0`, speeds clamped to `max_velocity`). Use `[extruder] min_extrude_temp` only when that key is present in config; do not invent `170`. If absent (and no `min_nozzle_temp` / `nozzle_temperature`), skip heat wait and **warn on the console**. Extruder operations (retract, fan) are also skipped in that case.
- Hints and profiles must not emit negative `wipe_z`. User may still be rejected by validation if unsafe.

## Source of truth

| Concern | Canonical location |
|---------|-------------------|
| Host version, log literals, host option keys | `plugin/klipper_common/constants.py` (`KLIPPER_COMMON_VERSION`) |
| Parse host keys | `__init__.py` `_parse_user_config` |
| Host defaults + `CommonSettings` | `defaults.py` `resolve_settings` |
| Host validation | `config_validate.py` `validate_common_config` |
| Host user/log strings | `messages.py` (`%` formatting only) |
| Feature registry | `features/__init__.py` |
| Prefix dispatch | `__init__.py` `load_config_prefix` |
| Wipe motion library (planner, hints, runner) | `features/wipe_motion/` |
| Bed wipe keys/defaults/G-code | `features/wipe_nozzle_on_bed/` |
| Rubber wipe keys/defaults/G-code | `features/wipe_nozzle_on_rubber/` |
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

## Architecture

- **Pure logic** (host `defaults` / `config_validate` / `messages` / `klipper_version` / `constants`; feature `constants` / resolve / validate / messages): **no** Klipper imports. Unit-test without a Klipper tree.
- **`__init__.py`**: host Klipper I/O, `register_command`, config parse, `get_status`, `load_config` / `load_config_prefix` wiring only.
- **Feature `feature.py` / `wipe_motion/runner.py` / `hints.py`**: may import Klipper.
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

This project is indexed by GitNexus as **klipper_common_plugin** (434 symbols, 678 relationships, 17 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
