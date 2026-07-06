# BOM sketch

The BOM below is a design target, not a shopping list yet.

## Core modules

| Item | Qty | Notes |
|---|---:|---|
| Main sheet-metal/plastic frame | 1 | supports paper path and service panels |
| Host board | 1 | Linux-capable SBC or custom compute module |
| Engine controller board | 1 | RP2040-class MCU, motor/sensor/LED/HV control |
| 24 V enclosed PSU | 1 | certified supply, power sized after fuser strategy |
| HV bias module | 1 | current-limited charge/develop/transfer rails |
| Fuser module | 1 | heater, thermistor, pressure roller, thermal fuse |
| Process cartridge module | 1 | OPC drum, developer, toner hopper, waste toner |
| LED exposure bar | 1 | 216 mm active width |
| Pickup roller assembly | 1 | replaceable sleeve |
| Separation pad | 1 | replaceable |
| Registration roller assembly | 1 | stepper-driven |
| Transfer roller | 1 | conductive compliant roller |
| Exit roller assembly | 1 | driven or gear-linked |
| Paper sensors | 5-7 | flag interrupter or reflective sensors |
| Cover interlock switches | 2 | hardware safety loop |
| Cooling fan | 1-2 | fuser/PSU airflow |
| Front panel board | 1 | buttons, LEDs/display |
| USB-C connector | 1 | device/service |
| Ethernet module/PHY | 1 | local network printing |

## Cost philosophy

Do not optimize the first build for cheapest possible BOM. Optimize for:

1. serviceability
2. understandable failure modes
3. available parts
4. sane assembly
5. no hidden consumable lockout

A printer that costs a bit more but can be repaired is the point.
