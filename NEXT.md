# Next engineering moves

## 1. Freeze the first physical rig: cold paper motion only

Build only the paper path, motors, sensors, frame, low-voltage PSU, and controller board. Do not install toner, fuser heater wiring, HV module, LED emitter rail, or process cartridge contacts in the first rig.

Pass/fail:

- 100 Letter sheets feed with no double-feed.
- Registration nip holds and releases the leading edge on command.
- `PRE_REG_SENSOR`, `IMAGE_SYNC_SENSOR`, `FUSER_EXIT_SENSOR`, and `EXIT_SENSOR` match the generated windows in `out/v2_motion_events.json`.
- Firmware can force all hazardous enables low even though those modules are not installed yet.

## 1b. Add the Rev G drum encoder before claiming line placement

Use `out/v2_motion_registration_budget.json` before any exposed-page rig. The nominal 62.0 mm/s process-speed constant is not enough: 0.5% open-loop error stretches Letter by about 33 lines.

Pass/fail:

- Drum encoder resolution is at least 4096 CPR quadrature, or 2048 CPR with timer interpolation that beats the quarter-line gate.
- LED line firing is slaved to measured drum phase, not only to a motor timer.
- Registration sensor edges are timestamped with <=150 µs jitter.
- A blank cold run logs encoder residuals for H12 drum-health analysis.

## 2. Build the LED timing jig

Use the 5120-pixel line model and a photodiode/logic-analyzer jig before any photoconductor or toner exists.

Pass/fail:

- 640-byte line payload shifts within 25% of the 682.8 µs line period.
- Latch and OE timing remain deterministic for one full Letter page.
- Output enable is removed by the hardware interlock gate, not just firmware.

## 2b. Run the OFP1 loopback before the LED jig carries real jobs

OFP1 is now defined (`docs/39_revE_ofp1_protocol.md`, `openframe_printer/ofp1.py`). Before the LED jig consumes host jobs, run host encoder against engine decoder over the real transport (USB serial), not just in-process.

Pass/fail:

- One full Letter page round-trips bit-exactly over the physical link at the 12 ppm line rate.
- Injected corruption (bit flips, truncated frames, mid-stream garbage) produces NACKs and a job fault, never a silently altered page.
- Worst-case page sustains its line rate with the engine ring buffer never emptying; if USB Full Speed cannot hold it on the bench, record it and spec High Speed, per `out/v2_ofp1_transport_budget.json`.
- `out/v2_ofp1_realtime_spool.json` passes the selected transport mode before the clutch starts: 12 ppm production uses USB High Speed or external page spool RAM; USB Full Speed service/debug mode uses slowed ppm and a larger prefilled ring.

## 2c. Run the Rev F halftone-floor loopback

Rev E's clustered-dot direction was correct, but the raw screen still emitted one-pixel partial seeds below the 4/64 highlight floor. Before a real LED bar exposes an OPC, run the host rasterizer through `openframe_printer/halftone.py` and verify generated printability artifacts.

Pass/fail:

- `out/v2_halftone_floor_gate.json` reports `revE_raw_screen_bug_reproduced: true` and `revF_screen_passes_floor_gate: true`.
- Requested tones below the 4/64 floor emit zero black pixels unless the job intentionally selects adaptive-minimum-dot experimental mode.
- Requested tones at and above the floor have zero isolated pixels and zero sub-2×2 black connected components.
- A printed grayscale ramp documents the visible highlight-floor cost before anyone claims continuous-tone performance.

## 2d. Run the H9 LED thermal feed-forward jig

`out/v2_led_thermal_feedforward.json` makes H9 executable but still model-based. Use a thermistor/IR camera or photodiode strip to compare blank, half-page, bar, and solid payloads over repeated pages.

Pass/fail:

- Black-heavy LED groups show measurably more thermal droop than blank groups.
- Payload-derived compensation stays within the generated pulse-width cap.
- Compensation reduces measured group-to-group optical error versus uncompensated output by at least 50% without creating overexposure in blank-adjacent regions.
- Residual errors are fed back into the PIDC rig instead of being hidden as a fixed global density adjustment.

## 2e. Run the Rev G LED optical MTF acceptance test

The LED bar can meet pixel-count and shift-clock requirements while failing latent-image contrast. Use `out/v2_optical_mtf_budget.json` before ordering the exposure bar.

Pass/fail:

- Supplier provides measured MTF >= 0.35 at 12 lp/mm at the OPC plane, or measured spot FWHM <=45 µm with <=15% one-pixel crosstalk.
- Slanted-edge/macro acceptance method repeats within the H13 tolerance before it replaces supplier optical data.
- A 50 µm or wider modeled spot remains a failing negative control in `scripts/model_tests.py`.

## 2f. Decide the Rev G LED-width / registration contract

Use `out/v2_registration_edge_budget.json` before freezing the exposure-bar RFQ. A 5120-pixel bar at 600 dpi is 216.747 mm wide, which leaves only 0.373 mm slack per side on Letter. That is not a 1 mm mechanical-registration budget.

Pass/fail:

- Either specify at least 5184 active pixels, or reduce guaranteed printable width to 214 mm.
- If keeping 5120 pixels for full-width Letter, prove lateral registration below +/-0.25 mm on the cold rig before exposing an OPC.
- Reject any test plan that treats +/-1 mm as print-quality acceptable; it is 23.6 lines at 600 dpi.

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
- Opening the active Rev F interlock path removes `HV_ENABLE_ACTUAL` without firmware cooperation.

## 3a. Prove Rev G HV stored-charge bleed-down

Use `out/v2_hv_discharge_bleed.json` and `hardware/ofp_m1_revG_process_safety_delta.csv`. Interlocks prove enables are removed; this test proves output nodes actually decay.

Pass/fail:

- With all bleeders installed, each HV node falls below 60 V within 2 s after disable / interlock trip.
- With one bleeder deliberately opened on each node, each output falls below 120 V within 2 s.
- The no-bleeder negative control remains a failing artifact in `out/v2_hv_discharge_bleed.json`.
- Bleeder power dissipation is measured at nominal and maximum HV output, not assumed from spreadsheet values alone.

## 3b. Build the H1 PIDC coupon rig

The calibration software closes in software (`out/v2_pidc_calibration_demo.json`); this rig replaces synthetic readings with a real probe. Use a drum or coupon on a grounded mandrel, the real LED bar segment, an electrostatic probe, humidity logging, and adjustable exposure-to-probe delay.

Pass/fail:

- Probe noise sigma ≤ 8 V, or rerun the demo with the actual probe sigma and still pass.
- Fitted PIDC predicts held-out probe readings within 25 V.
- Latent contrast retention ≥ 90% at 240 ms delay — the station-map-derived OPC accept/reject gate.

## 3b2. Add the Rev G erase/quench coupon test

Use `out/v2_erase_ghost_budget.json` before a full print engine run. The old process stack has no explicit erase station and now fails the ghost-memory gate.

Pass/fail:

- Install erase/quench after cleaning and before primary charge.
- Verify design dose near 0.75 µJ/cm² with the real source, slot, and process speed.
- Print or simulate an impulse band and measure residual contrast one drum circumference downstream, 94.25 mm on the 30 mm drum.
- Disable erase as the negative control; the test must become worse or it is not sensitive enough.

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

## 3d-env. Run the Rev G humidity/material derating sweep

Use `out/v2_environment_derating.json`. The engine cannot claim nominal settings across humidity and media until it has real density/background data.

Pass/fail:

- Log RH at the cartridge / paper path, not only room weather.
- Test 20%, 50%, and 80% RH with the candidate toner and paper.
- At 80% RH, run PIDC, developer-bias, and transfer sweeps before quality printing.
- Film/label media uses the explicit transfer offset as a starting center, then still obeys impedance-current clamps.

## 3e. Interlock fault-injection test before anything hazardous is energized

`out/v2_interlock_fault_analysis.json` now distinguishes three claims:

- Rev A single loop fails independent single faults.
- Rev E dual chain survives independent electrical stuck-at faults but fails a shared mechanical door-actuator/common-cause fault.
- Rev F topology C survives all modeled single faults by adding a physically diverse energy separator.

Build topology C from `hardware/interlock_chain.md` and `hardware/ofp_m1_revF_interlock_delta.csv`, then physically inject the faults the model enumerates.

Pass/fail:

- With any one contact bridged, any one loop shorted to its enable rail, any one gate output forced high, or any one shared door actuator wedged closed, opening any door still de-energizes HV, LED, and fuser paths.
- Firmware driving all requests high during every injected fault never re-energizes a hazard with a door open.
- Each injected electrical disagreement is detectable so a real weld does not wait silently for its partner fault.
- A welded energy separator alone is detected or logged as a service fault; topology C still needs the electrical chains because double faults remain dangerous.

## 4. Build the fuser thermal jig

Use `out/v2_fuser_sim.csv` for warm-up, `out/v2_fuser_power_balance.json` for continuous 12 ppm load, and `out/v2_fuser_thermal_safety.json` for runaway fault coverage. Rev F shows the warm-up model alone is not a throughput proof; Rev G shows firmware-only heat control is not a safety proof.

Pass/fail:

- Surface reaches 160 °C print-enable threshold without overshooting 195 °C.
- Heater power drops to zero when the thermostat loop opens.
- Heater power drops to zero when the one-shot fuse loop opens.
- Heater power drops to zero when firmware crashes or watchdog expires.
- Fault injection covers thermistor stuck cold, firmware output stuck on, SSR welded on, thermostat welded closed, and fuse bypass/open states from `out/v2_fuser_thermal_safety.json`.
- At nominal 75 gsm paper and the 12 ppm line rate, steady-state heater reserve is measured and compared with `out/v2_fuser_power_balance.json`.
- Damp/heavy media either slows the engine, increases allowed heater power/insulation, or rejects the job; it cannot silently run from the warm-up model.

## 4b. Run the Rev G fuser/exit emissions containment test

Use `out/v2_emissions_containment.json`. This is not a certification substitute; it is the gate that prevents an open plume around the fuser/output tray.

Pass/fail:

- Test uncontained, fan-filter-only, and source-plus-output-capture configurations.
- Measure around the fuser outlet, fan outlet, and output tray separately.
- Fan-filter-only must not be considered a pass unless measured emissions prove the high-emitter model pessimistic.
- No warm home-office rig runs without a serviceable capture/filter path and measured particle/ozone baseline.

## 5. Build the cold process-cartridge mechanical prototype

This is the first real cartridge geometry test, still without toner and without HV. Confirm the drum, developer roller, doctor blade mount, waste path, toner hopper, and spring contacts fit into the module envelope.

Pass/fail:

- OPC drum rotates at 39.47 rpm at 62.0 mm/s surface speed.
- Developer roller and drum center distances are adjustable by at least ±0.5 mm.
- Doctor blade gap can be set in the 80–180 µm sweep range.
- Cartridge can be removed without disturbing the paper path.

## 6. Only then combine subsystems

The real printer emerges when motion, LED timing, HV, fuser thermal control, interlocks, and the process cartridge are individually characterized. Combining them before those rigs pass is how printer projects turn into cursed smoke machines.
