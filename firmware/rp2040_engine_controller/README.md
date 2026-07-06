# RP2040 engine controller firmware skeleton

This firmware is the Rev A cold-rig controller skeleton.

It defaults every hazardous output off:

- `HV_ENABLE_REQUEST`
- `LED_OE_REQUEST`
- `LED_SAFE_EN_REQUEST`
- `FUSER_HEATER_REQUEST`
- `MAIN_MOTOR_ENABLE`

The firmware expects external hardware gates to enforce interlocks. Firmware permission alone is not enough to energize HV, LED output, fuser heat, or motors.

## Build idea

PlatformIO target from repo root:

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2/firmware/rp2040_engine_controller" && pio run
```

## Serial commands

```text
p = run one cold paper-motion cycle
r = reset fault back to idle
```

The skeleton exercises paper motion and line strobe timing only. It does not energize HV, fuser heat, or LED optical output.
