# 25. Open consumables spec

OpenFrame consumables are designed to be honest parts, not hostage mechanisms.

## Cartridge rules

- No cryptographic lockout.
- No cloud validation.
- No refusal to print because a cartridge is third-party.
- A resistor ID is allowed only to communicate cartridge family or capacity.
- User must be able to override non-safety warnings.
- Safety faults still stop printing.

## Toner container starting target

| Parameter | Value |
|---|---:|
| Toner mass | 80 g |
| Toner particle size | 6-8 µm |
| Dense black laydown model | 0.55 mg/cm² |
| Office coverage assumption | 5% |
| Theoretical calculated pages | about 2400 pages |

## Replacement parts

| Part | Sold directly | User replaceable | Service replaceable |
|---|---:|---:|---:|
| Toner/process cartridge | yes | yes | yes |
| Drum submodule | yes | yes | yes |
| Pickup roller kit | yes | yes | yes |
| Separation pad | yes | yes | yes |
| Transfer roller | yes | yes | yes |
| Fuser module | yes | no | yes |
| HV module | yes | no | yes |
| LED bar | yes | no | yes |
| Controller board | yes | no | yes |
| PSU | yes | no | yes |

## Service data exposed in UI

- Page count by module.
- Jam counts by sensor.
- Fuser warm-up time history.
- HV monitor values during calibration.
- Density calibration table.
- Firmware version.
- Last 50 fault events.
- Consumable warnings as warnings, not lockouts.
