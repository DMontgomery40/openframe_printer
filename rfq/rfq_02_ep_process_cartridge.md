# RFQ 02: EP process cartridge module

Document: OpenFrame M1 module RFQ  
Module ID: OF-M1-EPCART  
Revision: D, aligned to OpenFrame M1 Rev D engineering package  
Referenced platform docs: `docs/16_revA_engine_spec.md`, `docs/17_process_cartridge_mechanics.md`, `docs/19_hv_power_and_measurement.md`, `hardware/ofp_m1_revD_hv_bias_channels.csv`, `out/v2_station_map.json`, `out/v2_voltage_ladder.json`

## 1. What we are buying

A complete monochrome dry-electrophotographic process cartridge design for a new open printer platform: OPC drum, primary charge roller, developer roller, toner hopper, cleaning blade, and waste toner cavity in one user-replaceable module.

Hard platform requirement: **no consumable authentication lockout**. A passive resistor ID for cartridge family or capacity is acceptable only if the printer remains functional without it.

## 2. Required ratings

| Parameter | Requirement | Notes |
|---|---:|---|
| OPC drum diameter | 30.0 mm nominal | Rev A geometry is designed around this |
| Drum active coating width | at least 222 mm | 216 mm image plus edge margin |
| Process speed rating | 62.0 mm/s continuous | 12 ppm Letter target |
| Drum spectral sensitivity | state peak and range | must match candidate LED bars around 780 nm, with 660–780 nm acceptable range disclosed |
| OPC exposure sensitivity | disclose µJ/cm² response | package expects sensitivity data in µJ/cm², not mJ/cm² |
| Latent contrast hold | ≥90% retained at 240 ms | derived from the Rev C station map plus test margin |
| Rated life | at least 3000 pages drum, at least 1500 pages starter toner | state basis at 5% coverage |
| Toner | non-DRM black mono toner | state fusing window and particle size |
| Toner particle size | 6–8 µm target | disclose actual distribution |
| Dense black laydown | around 0.55 mg/cm² | used for yield and fuser sizing model |
| Waste capacity | at least toner charge life | no mid-life waste service |

## 3. Electrical / HV interface

The old −720 V PCR operating point is retired. Quote one of the following primary-charge options, or quote both as alternatives.

| Contact | Option | Operating point | Characterization range | Current limit |
|---|---|---:|---:|---:|
| Primary charge roller | A_dc_only | −1180 V DC | −900 to −1400 V | 200 µA |
| Primary charge roller | B_ac_dc | −600 V DC + 1.7 kVpp AC | DC −450 to −750 V; AC amplitude stated by supplier | 200 µA |
| Developer roller bias | selected | −320 V DC | −150 to −500 V | 300 µA |
| Developer monitor/sense | lab option | nanoamp-class induced-current measurement path preferred | supplier to state noise/current bandwidth | supplier to state |
| Cartridge ID resistor | passive only | 0–3.3 V sense | passive only | 1 mA |

Requirements:

- Contacts recessed and touch-safe when cartridge is handled.
- State drum ground return path.
- State expected charge-roller and developer current at operating points.
- Confirm no chip, EEPROM, or cryptographic device is required for printing.
- State whether the developer roller can be mechanically/electrically quiet enough to support a non-printing calibration read through `DEV_MON`.

## 4. Mechanical interface

| Item | Requirement |
|---|---|
| Cartridge envelope | 255 mm width, 92 mm depth, 86 mm height target |
| Datum | two datum pins plus one spring preload face |
| Drive | single keyed gear/coupler from process motor; state torque at 62.0 mm/s |
| Insertion | user-removable without tools, one motion, cannot be inserted wrong |
| Exposure window | open slot for stationary LED bar exposure at drum top quadrant |
| LED-to-development geometry | support the Rev C/D station map; selected OPC must hold latent contrast over the resulting delay |
| Shutter | drum light shutter preferred when module is out of machine |
| Part marking | visible public part number and date code |

## 5. Deliverables requested with quote

1. Outline drawing with datum, drive, contact, and exposure-window positions.
2. Drum photoconductor data: sensitivity curve, dark decay, residual potential, and latent-contrast retention at 90–240 ms delay.
3. Toner data: fusing window, particle size, charge polarity, storage limits.
4. Charge-roller option recommendation: DC-only raised bias versus AC+DC, with uniformity/noise/life tradeoffs.
5. Developer-roller electrical data: capacitance estimate, bias-current noise, and whether nanoamp induced-current measurement is realistic.
6. Sample pricing at 5, 25, 250, and 2500 pieces.
7. Toner refill pricing and refill procedure.
8. Rated life test data and end-of-life failure mode description.
9. Written confirmation that interface drawings may be published in an open service manual.

## 6. Acceptance tests

| Test | Pass criterion |
|---|---|
| Fit | datum seat and drive engage on first insertion; 25 insert/remove cycles without damage |
| Bias, Option A | charge roller reaches −1180 V inside current limit; developer reaches −320 V inside current limit |
| Bias, Option B | charge roller reaches −600 V DC plus specified AC amplitude; developer reaches −320 V inside current limit |
| OPC hold | ≥90% latent contrast retained at 240 ms delay on the H1 coupon rig |
| Developer-probe lab option | 8-step latent staircase is monotonic and resolves with ≥3σ separation if the option is claimed |
| Print quality rig | solid black density at least 1.2 OD, background fog less than 0.02 OD above paper |
| Life spot-check | no functional failure at 500 pages continuous on bench engine |
