# 52. Rev G fuser thermal safety model

Rev F added continuous fuser power balance. That still was not a runaway safety proof. Rev G makes the fuser cutoff stack executable.

Generated gate: `out/v2_fuser_thermal_safety.json`  
Executable model: `openframe_printer/fuser_safety.py`

## Finding

Firmware-only fuser heat control has three single-fault runaway paths in the Rev G model:

1. thermistor stuck cold,
2. firmware output stuck on,
3. SSR/relay welded on.

Those are enough to keep the heater live above the fault temperature if there is no independent cutoff in the heater energy path.

## Required topology

Rev G requires the fuser heater energy path to include:

```text
firmware-controlled switch
+ independent resettable thermostat / bimetal cutoff
+ independent one-shot thermal fuse
```

Generated result:

| Topology | Single-fault violations | Verdict |
|---|---:|---|
| firmware + thermistor + SSR only | 3 | fail |
| one independent thermostat | 0 in this model | pass single-fault, weaker backup |
| thermostat + one-shot fuse | 0 | pass single-fault and stronger abnormal-runaway backup |

## RFQ gate

A fuser module quote must include:

- thermistor curve,
- independent thermostat opening temperature,
- one-shot fuse functioning temperature,
- current and voltage ratings,
- physical proof that both cutoff loops are in series with heater energy.

This does not certify the appliance. It prevents the design package from pretending a PID loop is a safety device.

## Research anchors

- Thermal-cutoff application guidance treats a thermal cutoff as an independent over-temperature interrupt path. DigiKey's thermal-fuse guide describes the intended failure mode: when rated functioning temperature is exceeded, the device opens the circuit and breaks current flow. Rev G models the same principle as a fuser energy-path requirement rather than a firmware feature.
