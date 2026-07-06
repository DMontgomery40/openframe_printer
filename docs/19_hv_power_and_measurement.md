# 19. HV power and measurement

The HV system is a replaceable potted module controlled by the main board. The main board does not expose raw transformer windings or hand-built high-voltage multipliers. That is a deliberate service and safety choice for a real product.

Rev D supersedes the original Rev A PCR value. The old −720 V DC PCR target is a retired design input because it cannot produce the −600 V charged drum surface assumed by the exposure and development model. The generated model in `out/v2_hv_bias_channels.json` is now the authoritative HV table.

## Bias channels

| Channel | Option | Nominal | Characterization range | AC component | Current limit | Ramp |
|---|---|---:|---:|---:|---:|---:|
| PCR charge | A_dc_only | −1180 V DC | −900 to −1400 V | none | 200 µA | 400 V/s |
| PCR charge | B_ac_dc | −600 V DC | −450 to −750 V | 1.7 kVpp at ~1.5 kHz | 200 µA | 400 V/s |
| Developer bias | selected | −320 V DC | −150 to −500 V | none | 300 µA | 200 V/s |
| Transfer roller | selected_current_limited | +1600 V target | +700 to +2500 V | none | 500 µA | 500 V/s |

Only one PCR option is installed in a physical HV module. Option A is a DC-only supply redesign. Option B is an AC+DC charger and needs an AC stage with enough peak-to-peak voltage to exceed the charge-start threshold band with headroom.

## Control interface

| Signal | Type | Purpose |
|---|---|---|
| HV_ENABLE_HW | hardware-gated 3.3 V | Master enable after interlock AND gate |
| PCR_DAC | 0–3.3 V analog | PCR DC setpoint for Option A, or PCR DC component for Option B |
| PCR_AC_ENABLE | hardware-gated digital | Enable for Option B AC charger stage; absent/not-populated for Option A |
| DEV_DAC | 0–3.3 V analog | Developer bias setpoint |
| XFER_DAC | 0–3.3 V analog/current command | Transfer current/voltage command |
| PCR_MON | 0–3.3 V analog | Scaled PCR DC readback |
| PCR_AC_MON | scaled analog or comparator | Option B AC amplitude monitor; absent/not-populated for Option A |
| DEV_MON | scaled analog plus optional current-sense/TIA mode | Developer bias readback and Rev D H8 measurement channel |
| XFER_MON | scaled analog/current readback | Transfer voltage/current readback for impedance sniffing |
| HV_FAULT_N | open-drain digital | Module fault output |

## Required behavior

- Outputs ramp from zero; no step enable to final voltage.
- Outputs discharge through the module bleed path when disabled.
- Module faults if measured output does not track commanded output.
- Module faults if current exceeds the channel limit.
- Opening the cover removes `HV_ENABLE_HW` in hardware.
- Firmware cannot override the hardware interlock gate.
- Option B must fault if the AC component cannot meet the commanded kVpp amplitude.
- Transfer control must respect the 2500 V ceiling and 500 µA hardware limit even when impedance-sniffing paper.

## Artifact consistency gate

Before ordering or energizing an HV module, run:

```bash
python3 -m openframe_printer.design_report && python3 scripts/smoke_test.py && python3 scripts/model_tests.py
```

Pass condition:

- `out/v2_hv_consistency.json` has `all_checks_pass: true`.
- `out/v2_hv_bias_channels.json` contains PCR options `A_dc_only` and `B_ac_dc`.
- No generated PCR row has nominal −720 V.
- Option A nominal equals the ladder's −1180 V DC.
- Option B nominal equals the ladder's −600 V DC and AC amplitude equals the 1.7 kVpp Rev D spec.

## Dummy-load bench plan

Before connecting the process cartridge, use a dummy-load jig with safe enclosed HV test points and scaled monitor outputs.

| Test | Pass condition |
|---|---|
| PCR Option A ramp | reaches −1180 V target inside current limit and faults outside −900 to −1400 V |
| PCR Option B DC ramp | reaches −600 V DC target inside current limit and faults outside −450 to −750 V |
| PCR Option B AC amplitude | reaches 1.7 kVpp into the dummy load and faults below the commanded amplitude |
| Developer ramp | reaches −320 V target within monitor tolerance |
| Transfer normal impedance | reaches +1600 V target without exceeding current limit |
| Transfer high impedance | clamps at voltage ceiling and rejects/slows if current floor cannot be met |
| Interlock open | all outputs disabled independent of firmware |
| Simulated overcurrent | module asserts `HV_FAULT_N` and discharges |
| Power cycle | outputs remain off until command and interlock are valid |

## Service philosophy

The user should be able to replace the HV module as a part. They should not have to debug high-voltage analog circuitry inside the printer body. The design is open at the interface and module behavior level while still respecting that high voltage in a household appliance must be physically contained.
