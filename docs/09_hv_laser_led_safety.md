# HV, exposure, and safety

OpenFrame M1 uses high voltage biases and an optical exposure head. The design must fail safe.

## High-voltage rails

The HV module provides current-limited, interlock-gated rails for:

- primary charge roller
- developer bias
- transfer roller
- optional detack/discharge assist

Starting bias targets are in `hardware/hv_bias_targets.csv`.

## Safety requirements

| Requirement | Implementation |
|---|---|
| Cover open disables hazardous outputs | hardware interlock loop gates HV, LED, and fuser |
| Firmware cannot override cover-open state | interlock loop is physically in enable path |
| HV current is limited | module-level current limiting |
| Fuser over-temp has independent cutoff | thermal fuse in series with heater |
| LED/laser exposure enclosed | no user-accessible active optical path |
| Faults are latched | power cycle or explicit service reset required for hazardous faults |

## LED vs laser

M1 chooses LED exposure. If a future version uses a laser scanner, it needs a stricter optical safety design:

- enclosed beam path
- beam dump
- scan motor lock detection
- beam detect sanity check
- interlock disables laser diode current
- product-level laser classification review

LED exposure is not magically harmless, but it removes the spinning beam/scanner problem from the first build.

## No live-open service mode by default

The public service mode should never require running with covers removed. Factory/debug modes that energize hazardous rails with covers open must require hardware keys/jigs and should not be part of normal user service.
