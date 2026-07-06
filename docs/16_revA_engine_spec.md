# 16. OpenFrame M1 Rev A engine spec

This is the original v2 geometry and engine target. Earlier v1 values are superseded by this file and by `hardware/design_targets_revA.yaml`. Rev C/D supersedes the original Rev A HV charging assumptions; use `docs/19_hv_power_and_measurement.md`, `hardware/ofp_m1_revD_hv_bias_channels.csv`, and generated `out/v2_hv_bias_channels.json` for active HV values.

## Engine choice

OpenFrame M1 Rev A is a monochrome dry electrophotographic printer using a stationary LED printbar. The design avoids a spinning polygon laser scanner and avoids inkjet nozzle fabrication for the first product.

The machine still solves the actual printer problem: a repairable, local-first, documented printer with modular parts and no consumable lockout.

## Rev A numeric constants

| Parameter | Rev A target |
|---|---:|
| Resolution | 600 dpi |
| Print mode | 1-bit monochrome |
| LED pixels | 5120 |
| LED pitch | 42.333 µm |
| LED active width | 216.747 mm |
| Letter speed | 12 ppm |
| Letter page length | 279.4 mm |
| Inter-page gap | 30.6 mm |
| Process speed | 62.0 mm/s |
| Line rate | 1464.567 lines/s |
| Line period | 682.796 µs |
| Line payload | 640 bytes |
| OPC drum diameter | 30.0 mm |
| OPC drum circumference | 94.248 mm |
| OPC drum speed | 39.47 rpm |
| Fuser hot roller diameter | 24.0 mm |
| Fuser nip width | 5.0 mm |
| Fuser nip dwell | 80.6 ms |
| Fuser nominal surface temp | 178 °C |

## Imaging stack order

1. Primary charge roller uniformly charges the OPC drum.
2. LED printbar discharges image pixels line by line.
3. Developer roller presents charged toner to the latent image.
4. Transfer roller pulls toner from drum to paper.
5. Fuser melts and presses toner into the sheet.
6. Cleaner/waste path removes residual toner before the next drum revolution.

## Rev A design rationale

A 30 mm OPC drum is intentionally less aggressive than the smaller v1 24 mm target. The larger drum reduces curvature sensitivity, lowers rpm at the same process speed, and gives more mechanical room around charge, exposure, development, transfer, and cleaning stations.

A 5120-pixel LED bar is intentionally wider than the 5102 pixels needed to span 216.0 mm at 600 dpi. The extra width gives registration and edge-margin slack while keeping the line payload exactly 640 bytes.

## Core module boundaries

| Module | User replaceable | Service replaceable | Notes |
|---|---:|---:|---|
| Process cartridge | yes | yes | OPC drum, developer roller, toner hopper, waste path |
| Transfer roller | yes | yes | Separable from cartridge to avoid needless replacement |
| Fuser module | no | yes | Hot module with thermal fuse and thermostat |
| Paper pickup/separation kit | yes | yes | Rollers, separation pad, tray wear parts |
| LED bar | no | yes | Factory-calibrated optical module |
| Controller board | no | yes | Open pinout and firmware |
| HV module | no | yes | Potted current-limited replaceable module |
| Low-voltage PSU | no | yes | Isolated replaceable module |

## Calibration surfaces

Rev A needs calibration sweeps instead of fixed magic constants:

| Calibration | Initial sweep |
|---|---|
| LED exposure energy | 0.15, 0.25, 0.35, 0.45, 0.60, 0.80, 1.00 µJ/cm² |
| Primary charge | Rev D Option A: −900 to −1400 V DC; Rev D Option B: −450 to −750 V DC plus 1.7 kVpp AC |
| Developer bias | -150 to -500 V |
| Transfer bias | +700 to +2500 V |
| Doctor blade gap | 80 to 180 µm |
| Fuser surface temp | 165 to 190 °C |

The first good print is expected to come from sweeping these variables in a controlled jig, not from guessing one perfect value.


## Rev D supersession note

The mechanical constants above remain the first-build geometry. The original Rev A primary-charge sweep is not active because a −720 V DC charge roller cannot create the −600 V drum surface assumed by the rest of the electrophotographic stack. Active HV requirements live in the Rev D HV table and generated artifacts.
