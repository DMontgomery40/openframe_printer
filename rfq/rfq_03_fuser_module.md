# RFQ 03: Fuser module

Document: OpenFrame M1 module RFQ  
Module ID: OF-M1-FUSER  
Revision: B, aligned to OpenFrame M1 Rev A v2  
Referenced platform docs: `docs/20_fuser_module_detail.md`, `hardware/design_targets_revA.yaml`

## 1. What we are buying

A replaceable monochrome laser-printer-style fuser module for a new open printer platform.

## 2. Required ratings

| Parameter | Requirement |
|---|---:|
| Process speed | 62.0 mm/s |
| Hot roller diameter | 24 mm target |
| Pressure roller diameter | 24 mm target |
| Nip width | 5.0 mm target |
| Nip dwell | 80.6 ms at process speed |
| Nominal surface temp | 178 °C |
| Printable temp threshold | 160 °C |
| Warning threshold | 195 °C |
| Firmware fault threshold | 205 °C |
| Heater power starting target | 800 W |
| Thermal fuse | one-shot independent cutoff required |
| Thermostat | independent bimetal cutoff required |
| Thermistor | analog temperature readback required |

## 3. Connector requirement

| Signal | Requirement |
|---|---|
| Heater line switched | relay/SSR controlled, safety-rated |
| Heater neutral | safety-rated |
| Thermistor pair | isolated from heater |
| Thermostat loop | normally closed |
| Thermal fuse loop | normally closed until one-shot event |
| Tach | fuser roller motion confirmation preferred |
| Protective earth | bond to metal fuser structure |

## 4. Deliverables requested with quote

1. Outline drawing and mounting method.
2. Heater power and warm-up curve.
3. Thermistor curve.
4. Thermostat and thermal fuse ratings.
5. Roller coating material and toner compatibility.
6. Expected life and failure modes.
7. Sample pricing at 5, 25, 250, and 2500 pieces.
8. Confirmation that interface drawings may be published in an open service manual.

## 5. Acceptance tests

| Test | Pass criterion |
|---|---|
| Warm-up | reaches print-enable threshold without exceeding warning threshold |
| Overtemp | independent thermostat opens heater circuit |
| Fuse | one-shot thermal fuse opens on abnormal runaway test |
| Paper transport | 100 sheets pass through fuser nip without accordion jam |
| Rub test | toner remains fused after normal cooling at nominal temp |
