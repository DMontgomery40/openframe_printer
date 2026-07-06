# Module interface contract

OpenFrame should have stable internal module contracts so parts can improve without breaking the platform.

## Process cartridge module

Contains:

- OPC drum
- charge roller contact
- developer roller
- toner hopper
- cleaning/waste path
- mechanical datum surfaces

External interfaces:

| Interface | Requirement |
|---|---|
| Mechanical | two datum pins, one spring preload face |
| Drive | keyed gear/coupler from process motor |
| HV contacts | charge, developer, optional discharge; recessed touch-safe contacts |
| Toner ID | optional passive resistor/EEPROM for capacity estimate only; must not lock out printing |
| Service | user-removable without tools |

## LED exposure bar module

External interfaces:

| Interface | Requirement |
|---|---|
| Mechanical | datum pin pair, shim pads, spring preload |
| Electrical | VLED, logic power, data, clock, latch/strobe, output enable, fault |
| Calibration | per-bar correction table stored on host/control board |
| Service | technician-replaceable with calibration page |

## Fuser module

External interfaces:

| Interface | Requirement |
|---|---|
| Mechanical | captive screws, keyed hot-zone handling |
| Power | separated heater connector, touch-safe, keyed |
| Sensors | thermistor, thermal fuse continuity, optional tach |
| Drive | gear/coupler or dedicated motor |
| Service | technician-replaceable after cool-down |

## Paper feed module

External interfaces:

| Interface | Requirement |
|---|---|
| Pickup roller sleeve | user-replaceable |
| Separation pad | user-replaceable |
| Sensor | tray present and pickup confirmation |
| Adjustment | no hidden calibration unless absolutely necessary |
