# 26. Compliance and safety plan

This repo is not a certification file. It is the design package that must become one.

## Hazards

| Hazard | Source | Design control |
|---|---|---|
| Electric shock | mains input, fuser heater, HV bias rails | protective earth, isolation, fuses, potted HV module, interlock loop |
| Burn/fire | fuser hot roller and heater | thermistor, thermostat, thermal fuse, firmware timeout, flame-retardant materials |
| Eye/skin light exposure | LED exposure bar | enclosed optical path, cover interlock, LED OE hardware gate |
| Mechanical pinch | rollers and gears | covers, interlocks, low-force accessible areas |
| Toner dust | cartridge and waste path | sealed cartridge, gaskets, service instructions |
| Smoke/odor | fuser and media | temp limits, paper path monitoring, fan control |

## Hardware-gated outputs

- `HV_ENABLE_HW`
- `LED_OE_HW`
- `FUSER_HEATER_ENABLE_HW`
- `MAIN_MOTOR_ENABLE`

Firmware may request these outputs, but hardware interlocks decide whether they can actually turn on.

## Materials targets

- Fuser-adjacent plastics: high-temperature, flame-retardant grade.
- Toner seals: replaceable elastomer strips compatible with toner chemistry.
- Paper path guides: low-friction, toner-compatible polymer or coated metal.
- Chassis: metal or grounded conductive structure near fuser/HV zones.

## Certification work packages

1. Electrical insulation and creepage/clearance review.
2. Protective earth bond test.
3. Abnormal fuser runaway test.
4. Interlock defeat resistance review.
5. Flammability material review.
6. EMC pre-scan.
7. Toner emissions/dust review.
8. User/service documentation review.

The design needs qualified review before any powered appliance prototype enters a home or office.
