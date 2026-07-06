# 08. Thermal fuser

This file is superseded by `docs/20_fuser_module_detail.md` for Rev A details.

## Rev A target

| Parameter | Value |
|---|---:|
| Hot roller diameter | 24 mm |
| Pressure roller diameter | 24 mm |
| Nip width | 5.0 mm |
| Process speed | 62.0 mm/s |
| Nip dwell | 80.6 ms |
| Nominal surface temperature | 178 °C |
| Print-enable threshold | 160 °C |
| Warning threshold | 195 °C |
| Firmware fault threshold | 205 °C |
| Heater power starting target | 800 W |

## Required safety chain

The fuser heater is controlled by firmware during normal operation but must also be limited by independent hardware:

1. fuse,
2. cover/interlock loop,
3. relay or SSR,
4. thermostat,
5. one-shot thermal fuse,
6. grounded fuser frame.

The first physical rig does not energize the fuser heater.
