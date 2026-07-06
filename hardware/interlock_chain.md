# Interlock chain

Minimum interlock design:

```text
COVER_SWITCH_1_NC ---- COVER_SWITCH_2_NC ---- SERVICE_PANEL_NC ---- INTERLOCK_LOOP_OK
```

`INTERLOCK_LOOP_OK` is used two ways:

1. Read by the MCU so firmware can explain the fault.
2. Wired into hardware enable gates so hazardous outputs turn off even if firmware fails.

## Gated outputs

```text
HV_ENABLE_ACTUAL     = HV_ENABLE_REQ     AND INTERLOCK_LOOP_OK AND HV_MODULE_OK
LED_OE_ACTUAL        = LED_OE_REQ        AND INTERLOCK_LOOP_OK
FUSER_ENABLE_ACTUAL  = FUSER_REQ         AND INTERLOCK_LOOP_OK AND THERMAL_FUSE_OK AND OVERTEMP_GATE_OK
```

## Fault behavior

If interlock loop opens:

- fuser heater disabled
- HV disabled
- LED output disabled
- motors may coast/stop depending safe jam strategy
- job aborted
- fault latched until cover closes and user acknowledges
