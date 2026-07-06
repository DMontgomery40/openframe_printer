# 55. Rev G HV stored-charge bleed-down

Rev E/F interlock work proves hazardous enables are removed under modeled access-door faults. That still does not prove high-voltage outputs become safe to touch. An HV node with output capacitance and no deliberate discharge path can stay charged after the interlock opens.

Rev G adds `openframe_printer/hv_discharge.py` and `out/v2_hv_discharge_bleed.json`.

## Generated counterexample

The no-bleeder case is now a first-class failing artifact:

```text
initial voltage: 2500 V
capacitance: 2.2 nF
stored energy: 6.875 mJ
voltage after 2 s with no specified bleed path: 2500 V
verdict: fail_no_guaranteed_touch_safe_decay
```

## Research / safety basis

The bleed-down gate follows the same shape as IEC 62368-style capacitor-discharge language: below 60 V within 2 seconds normally, and below 120 V within 2 seconds under a single fault such as an open bleeder. This package is not a certification, but the modeled requirement now points at a real safety test instead of relying on interlock prose.

## Active bleeder requirement

Every HV output node gets two independent HV-rated bleeders. The generated table verifies normal discharge below 60 V and single-fault discharge below 120 V after 2 s.

```text
TRANSFER_ROLLER_OUTPUT:        2 × 100 MΩ, 2.2 nF, passes
PCR_DC_OUTPUT_OPTION_A:        2 × 100 MΩ, 2.2 nF, passes
PCR_AC_PEAK_OUTPUT_OPTION_B:   2 × 150 MΩ, 1.0 nF, passes
DEVELOPER_BIAS_OUTPUT:         2 × 220 MΩ, 1.0 nF, passes
```

The test is intentionally independent of firmware. Opening a door or removing mains must be followed by a measured decay check on each HV node. A single open bleeder is part of the generated negative-control model, not an afterthought.
