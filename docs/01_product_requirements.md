# 01. Product requirements

OpenFrame M1 is a new repairable local-first monochrome printer platform.

## Non-negotiables

- No cloud account required.
- No phone app required.
- No consumable authentication lockout.
- Public service manual.
- Public module interface docs.
- Direct replacement parts.
- Local IPP/AirPrint/Mopria support.
- Exact fault messages tied to sensors/modules.

## Rev A product target

| Requirement | Rev A target |
|---|---:|
| Print technology | monochrome dry electrophotographic LED |
| Resolution | 600 x 600 dpi |
| Speed | 12 ppm Letter |
| Media | Letter/A4 plain paper |
| Paper weight | 60-105 gsm |
| Tray | 250 sheets at 80 gsm |
| First page out | measured after fuser thermal rig; target under 15 s from warm state |
| Duty cycle | initial engineering target 3000 pages/month |
| Connectivity | USB and Ethernet first; Wi-Fi module as replaceable option |
| Driver path | IPP Everywhere/AirPrint/Mopria |

## Repairability requirements

| Part | User replaceable | Service replaceable |
|---|---:|---:|
| Toner/process cartridge | yes | yes |
| Drum submodule | yes | yes |
| Pickup roller kit | yes | yes |
| Separation pad | yes | yes |
| Transfer roller | yes | yes |
| Fuser module | no | yes |
| HV module | no | yes |
| LED bar | no | yes |
| PSU | no | yes |
| Controller board | no | yes |

## Open consumables rules

- Printer must not refuse to print because of cartridge identity.
- Passive ID is allowed for user information only.
- Warnings are allowed; lockouts are only allowed for safety faults.
- Calibration values must be exportable.
- Compatible consumables must be mechanically and electrically spec-able from public docs.
