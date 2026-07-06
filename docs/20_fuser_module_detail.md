# 20. Fuser module detail

The fuser is a replaceable hot module. It is not a casual user-service part because it combines mains voltage, high temperature, spring pressure, paper dust, and polymer materials.

## Rev A thermal constants

| Parameter | Rev A target |
|---|---:|
| Hot roller diameter | 24 mm |
| Pressure roller diameter | 24 mm |
| Nip width | 5.0 mm |
| Process speed | 62.0 mm/s |
| Nip dwell | 80.6 ms |
| Nominal surface temperature | 178 °C |
| Print-enable surface temperature | 160 °C |
| Warning threshold | 195 °C |
| Firmware fault threshold | 205 °C |
| Heater power starting target | 800 W |

## Independent safety chain

The heater enable must pass through all of these, in hardware:

1. Mechanical power switch and fuse.
2. Cover/interlock loop.
3. Firmware-controlled relay/SSR gate.
4. Independent thermostat loop.
5. One-shot thermal fuse.
6. Heater element.

Firmware controls normal temperature. Hardware prevents runaway when firmware is wrong.

## Thermal model

The generated file `out/v2_fuser_sim.csv` uses:

| Model parameter | Value |
|---|---:|
| Ambient | 25 °C |
| Heater power | 800 W |
| Heat capacity | 460 J/°C |
| Thermal resistance | 0.235 °C/W |
| Control period | 0.1 s |
| Target | 178 °C |

This model is only a first-order sizing model. The actual module needs thermistor placement validation, roller surface measurement, and paper-load testing.

## Service design

- Fuser module is held by two captive screws and one keyed connector.
- Connector includes heater line, heater neutral, thermistor pair, thermostat loop, thermal fuse loop, tach, and PE bond.
- The printer refuses to energize the fuser if thermistor reading is implausible.
- A blown thermal fuse marks the fuser module as service-required.
