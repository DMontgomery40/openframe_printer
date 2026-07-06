# 23. Rev A DFMEA

This is the first design-failure-mode map for a new OpenFrame printer.

| Subsystem | Failure mode | Effect | Detection | Design response |
|---|---|---|---|---|
| Pickup | no pickup | blank feed attempt, user frustration | paper sensor and pre-reg timeout | replaceable pickup roller kit |
| Separation | double-feed | jam or two sheets through engine | pre-reg timing plus thickness/skew option | replaceable separation pad |
| Registration | late release | image starts in wrong place | image sync timing error | stop imaging, eject sheet |
| LED bar | missing line | horizontal white stripe | built-in test pattern and photodiode jig | service-replace LED bar |
| LED bar | overtemp | density drift, LED damage | LED_TEMP_NTC | reduce duty, fault if high |
| PCR charge | low charge | gray background/fog | HV monitor and density page | bias sweep and service message |
| Developer | low density | faint print | density calibration page | documented developer bias and doctor blade setup |
| Transfer | weak transfer | toner left on drum | density page and transfer monitor | transfer bias sweep, replace transfer roller |
| Fuser | under-temp | toner rubs off | thermistor and rub test | block printing below print-enable temp |
| Fuser | over-temp | fire/smoke risk | thermistor, thermostat, thermal fuse | hardware removes heater enable |
| Firmware | crash | outputs stuck if not gated | watchdog | hardware gates all hazardous enables |
| Cover | opened during print | user exposure to hot/HV/light areas | cover loop | hardware removes HV/LED/fuser enable |
| Cartridge | toner leak | contamination and poor print | service inspection, density drift | replace gaskets or cartridge module |
| HV contact | poor contact | missing charge/develop/transfer | HV monitor and print defect pattern | replace spring contact block |
| Exit path | paper remains | jam/fire risk near fuser | exit sensor stuck active | fuser off, fans on, user clear message |

## Highest-risk items

1. Fuser runaway.
2. HV exposure during service.
3. Toner/developer stability.
4. Paper skew through transfer/fuser.
5. LED exposure uniformity.
6. Consumable leakage.

## Design rules from the DFMEA

- All hazardous outputs are hardware-gated.
- All wear parts are reachable without disassembling the frame.
- Error messages name the sensor or module that failed.
- Calibration values are visible and exportable.
- Parts are identified by open mechanical/electrical interface, not lockout chips.
