# Next engineering moves

## 1. Freeze the first physical rig: cold paper motion only

Build only the paper path, motors, sensors, frame, low-voltage PSU, and controller board. Do not install toner, fuser heater wiring, HV module, LED emitter rail, or process cartridge contacts in the first rig.

Pass/fail:

- 100 Letter sheets feed with no double-feed.
- Registration nip holds and releases the leading edge on command.
- `PRE_REG_SENSOR`, `IMAGE_SYNC_SENSOR`, `FUSER_EXIT_SENSOR`, and `EXIT_SENSOR` match the generated windows in `out/v2_motion_events.json`.
- Firmware can force all hazardous enables low even though those modules are not installed yet.

## 2. Build the LED timing jig

Use the 5120-pixel line model and a photodiode/logic-analyzer jig before any photoconductor or toner exists.

Pass/fail:

- 640-byte line payload shifts within 25% of the 682.8 µs line period.
- Latch and OE timing remain deterministic for one full Letter page.
- Output enable is removed by the hardware interlock gate, not just firmware.

## 3. Build the potted-HV dummy-load jig

Use `hardware/ofp_m1_revD_hv_bias_channels.csv` and generated `out/v2_hv_bias_channels.json`, not the historical Rev A HV table. The Rev A PCR target (−720 V) is retired: the voltage ladder shows it cannot charge the drum to the −600 V the exposure and development model assumes. Pick charging Option A or Option B before specifying the HV module:

- Option A: DC-only PCR, −1180 V nominal, −900 to −1400 V range.
- Option B: AC+DC PCR, −600 V DC plus 1.7 kVpp AC at roughly 1–2 kHz.

The dummy-load jig proves ramping, monitoring, current limiting, discharge behavior, and artifact consistency without a process cartridge.

Pass/fail:

- `python3 -m openframe_printer.design_report && python3 scripts/smoke_test.py` passes before any HV module is ordered.
- `out/v2_hv_consistency.json` reports `all_checks_pass: true`.
- PCR channel ramps to the chosen Rev D option's target and faults outside range.
- Developer channel ramps to −320 V target and faults outside range.
- Transfer channel ramps to +1600 V target and faults outside range under a normal dummy load.
- Opening `COVER_CLOSED_LOOP` removes `HV_ENABLE_HW` without firmware cooperation.

## 3b. Build the H1 PIDC coupon rig

The calibration software closes in software (`out/v2_pidc_calibration_demo.json`); this rig replaces synthetic readings with a real probe. Use a drum or coupon on a grounded mandrel, the real LED bar segment, an electrostatic probe, humidity logging, and adjustable exposure-to-probe delay.

Pass/fail:

- Probe noise sigma ≤ 8 V, or rerun the demo with the actual probe sigma and still pass.
- Fitted PIDC predicts held-out probe readings within 25 V.
- Latent contrast retention ≥ 90% at 240 ms delay — the station-map-derived OPC accept/reject gate.

## 3c. Build the H8 developer-probe electronics jig

This is not a print rig. It validates whether the developer roller can act as an in-situ electrostatic probe. Use `out/v2_dev_probe_budget.json` as the numeric target. The default 64×64 patch produces only a few nanoamps; the first realistic jig should use 128×128-pixel patches and a dedicated DEV_MON current-sense/TIA path.

Pass/fail:

- With 128×128-pixel patches, the induced staircase is monotonic across 8 exposure steps.
- DEV_MON equivalent input noise is ≤ 0.5 nA RMS in the measurement bandwidth, or the patch size/noise budget is recomputed and still resolves the steps with 3σ separation.
- The induced staircase correlates with an external electrostatic probe reading on the same latent staircase.
- Reject H8 for production if it requires lab-grade external instrumentation, corrupts developer bias stability, or loses monotonicity with toner installed.

## 3d. Build the transfer impedance sniff jig

Use `out/v2_transfer_impedance_plan.json` as the starting control law. Before a real image transfer, inject a limited diagnostic transfer current through a non-image lead-in zone or sacrificial strip, estimate paper/nip impedance from measured voltage/current, then choose transfer current with voltage and current clamps.

Pass/fail:

- Normal dummy impedances from 8 MΩ to 300 MΩ choose a valid transfer current and remain at or below the 2500 V transfer ceiling.
- The 800 MΩ extreme case rejects or slows the engine instead of silently accepting a likely under-transfer condition.
- The transfer module never exceeds the 500 µA hardware channel current limit.

## 4. Build the fuser thermal jig

Use the thermal model in `out/v2_fuser_sim.csv` as the starting expectation. The fuser jig needs two independent temperature measurements, a thermostat, and a one-shot thermal fuse.

Pass/fail:

- Surface reaches 160 °C print-enable threshold without overshooting 195 °C.
- Heater power drops to zero when the thermostat loop opens.
- Heater power drops to zero when firmware crashes or watchdog expires.

## 5. Build the cold process-cartridge mechanical prototype

This is the first real cartridge geometry test, still without toner and without HV. Confirm the drum, developer roller, doctor blade mount, waste path, toner hopper, and spring contacts fit into the module envelope.

Pass/fail:

- OPC drum rotates at 39.47 rpm at 62.0 mm/s surface speed.
- Developer roller and drum center distances are adjustable by at least ±0.5 mm.
- Doctor blade gap can be set in the 80–180 µm sweep range.
- Cartridge can be removed without disturbing the paper path.

## 6. Only then combine subsystems

The real printer emerges when motion, LED timing, HV, fuser thermal control, and the process cartridge are individually characterized. Combining them before those rigs pass is how printer projects turn into cursed smoke machines.
