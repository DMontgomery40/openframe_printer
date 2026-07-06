# 37. Rev D transfer impedance control

The original package treated transfer as a fixed voltage target. Rev D keeps the +1600 V nominal target but stops assuming that every sheet/nip state behaves the same. The transfer station should estimate paper/nip impedance first, then choose a current-limited command that lands near the target field without violating voltage or current limits.

Implementation lives in `openframe_printer/transfer_model.py` and emits `out/v2_transfer_impedance_plan.json`.

## Control law

For a measured paper/nip impedance `Z` in MΩ:

```text
I_target_µA = V_target / Z_MΩ
V_command = clamp(I_target * Z, V_min, V_max)
I_command = clamp(I_target, I_min, I_max)
```

Rev D defaults:

| Parameter | Value |
|---|---:|
| Target transfer voltage | +1600 V |
| Voltage ceiling | +2500 V |
| Current floor | 5 µA |
| Current ceiling | 200 µA command, 500 µA hardware limit |

## Scenario output

| Scenario | Impedance | Command | Result |
|---|---:|---:|---|
| humid/low-resistance paper | 8 MΩ | 200 µA | run; lands at target voltage |
| normal office paper | 30 MΩ | 53.3 µA | run |
| dry/heavy paper | 100 MΩ | 16.0 µA | run |
| very dry paper | 300 MΩ | 5.33 µA | run |
| extreme dry/insulating state | 800 MΩ | voltage-limited at 2500 V | reject or slow engine |

## Why reject/slow exists

At extreme impedance, commanding the nominal target would require less current than the current floor. Raising voltage to the 2500 V ceiling still may not provide enough transfer current. The correct behavior is to reject, slow the engine, or require a different transfer strategy — not to pretend the page transferred correctly.

## Test

Use a dummy transfer nip and selectable impedance loads before toner exists.

Pass:

- 8–300 MΩ dummy states choose valid current commands without exceeding 2500 V.
- 800 MΩ dummy state enters `reject_or_slow_engine_for_transfer_latitude`.
- Current never exceeds the 500 µA hardware channel limit.
- `XFER_MON` reports enough voltage/current data to recompute impedance.

Fail:

- Controller commands fixed +1600 V without reading impedance.
- Extreme impedance silently prints.
- Transfer current command can exceed hardware current limit.

## Research anchors

- Transfer control patents describe measuring transfer roll voltage/current and adjusting current based on paper/roller impedance for stable transfer.
- Paper moisture and electric field strength affect toner transfer quality; paper/substrate properties affect transfer efficiency and image evenness.

Sources used during Rev D research: `https://patents.google.com/patent/US5124759A/en`, `https://patents.google.com/patent/US5862422A/en`, and print-transfer literature on paper moisture/electric field effects.
