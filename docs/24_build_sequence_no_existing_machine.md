# 24. Build sequence for a new machine

This is the build sequence for creating OpenFrame M1 as a new printer.

## Rig 1: cold paper-motion rig

Installed:

- frame,
- tray,
- pickup roller,
- separation pad,
- registration roller,
- paper sensors,
- low-voltage PSU,
- MCU/controller,
- motors.

Not installed:

- toner,
- OPC drum coating,
- HV module,
- fuser heater wiring,
- LED emitter power.

Goal: prove paper motion and sensor timing.

## Rig 2: LED timing rig

Installed:

- controller,
- LED bar electrical interface,
- photodiode or logic analyzer capture jig.

Goal: prove deterministic line timing at 600 dpi and 12 ppm.

## Rig 3: HV dummy-load rig

Installed:

- potted HV module,
- scaled monitors,
- interlock loop,
- dummy loads,
- discharge confirmation.

Goal: prove bias control, current limiting, interlock shutdown, and fault behavior.

## Rig 4: fuser thermal rig

Installed:

- fuser module,
- thermistor,
- thermostat,
- thermal fuse,
- tach,
- fans,
- interlock loop.

Goal: prove warm-up, temperature control, and independent cutoff.

## Rig 5: cold process-cartridge rig

Installed:

- OPC drum mechanical blank,
- developer roller mechanical blank,
- doctor blade holder,
- waste path,
- spring contacts without HV.

Goal: prove cartridge insertion, alignment, rotation, service access, and paper clearance.

## Rig 6: first imaging rig

Installed:

- charged OPC test drum,
- LED exposure,
- HV under interlock,
- no toner at first.

Goal: verify latent-image exposure behavior before adding developer toner.

## Rig 7: first print rig

Installed:

- toner/developer,
- transfer roller,
- fuser,
- full interlocks,
- full sensors.

Goal: print density wedge pages and lock the first calibration table.
