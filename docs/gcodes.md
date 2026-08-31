# G-codes — Klipper Common Plugin

Install / config: [install.md](install.md) · [configuration.md](configuration.md).

Feature commands are documented with that feature (registered only when its section is present).

## Host

| Command | Purpose | When registered |
|---------|---------|-----------------|
| `COMMON_STATUS` | Report plugin version, Klipper version, `log_level`, and enabled feature G-codes | `[klipper_common]` |
| `COMMON_VERSION` | Report plugin version only | `[klipper_common]` |

No extra parameters.

```gcode
COMMON_STATUS
# klipper_common: version=0.0.1 klipper=v0.13.0-… log_level=info

COMMON_VERSION
# klipper_common 0.0.1
```

## Features

| Command | Doc |
|---------|-----|
| `WIPE_NOZZLE_ON_BED` | [features/wipe_nozzle_on_bed.md](features/wipe_nozzle_on_bed.md) |
| `WIPE_NOZZLE_ON_RUBBER` | [features/wipe_nozzle_on_rubber.md](features/wipe_nozzle_on_rubber.md) |
| `FORM_TIP` | [features/form_tip.md](features/form_tip.md) |
| `PURGE_ON_BED` | [features/purge_on_bed.md](features/purge_on_bed.md) |
| `PURGE_AT_POSE` | [features/purge_at_pose.md](features/purge_at_pose.md) |
| `PAUSE` `RESUME` `CANCEL_PRINT` | [features/pause_resume.md](features/pause_resume.md) |

`[klipper_common hook]` does not register a command. See [features/hook.md](features/hook.md).
