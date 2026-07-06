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


## Rev G transport and motion notes

The OFP1 decoder being CRC-clean is not enough to start a page. Before enabling the registration clutch, firmware must prove the decoded-line buffer margin from `out/v2_ofp1_realtime_spool.json`.

Line strobes should be driven from the Rev G drum-encoder phase model in `out/v2_motion_registration_budget.json`; the registration sensor sets the lead-edge phase only.
