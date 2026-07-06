# OpenFrame Printer Newbuild v2

OpenFrame M1 is a from-scratch modular printer design package. It is **not** a conversion layer, bridge appliance, or modified existing printer. The v2 package pushes the idea toward a real new machine: engine constants, HV channel targets, LED bar timing, process-cartridge geometry, fuser thermal model, paper-path timing, connector maps, interlock matrix, and a future inkjet/nozzle R&D branch.

## Primary build target

**OpenFrame M1 Rev E package, derived from the original Rev A geometry**

- Technology: monochrome dry electrophotographic printer with a stationary LED exposure bar
- Print mode: 1-bit monochrome, 600 dpi
- Speed target: 12 ppm Letter
- Active LED bar: 5120 pixels, 42.333 µm pitch, 216.747 mm active width
- Process speed: 62.0 mm/s
- OPC drum: 30.0 mm diameter
- Fuser target: 178 °C surface temp, 5.0 mm nip, 80.6 ms dwell at process speed
- Print path: IPP/AirPrint/Mopria externally, deterministic OFP1 raster/engine protocol internally
- Business/model constraint: public service docs, public module interfaces, direct replacement parts, no cartridge DRM lockout, no cloud requirement

## What changed in v2

- Locked a **Rev A architecture** around a new 30 mm OPC drum and 5120-pixel LED bar.
- Added exact connector maps for power, motors, sensors, LED bar, HV module, cartridge contacts, fuser, and UI.
- Added HV bias channel table with nominal/range/current-limit/ramp targets.
- Added fuser thermal model with generated warm-up CSV.
- Added motion timing model with jam windows and sensor positions.
- Added process cartridge cross-section, cartridge requirements, and open consumables spec.
- Added inkjet/nozzle R&D constants so the nozzle path is mapped, while keeping the first build on the easier monochrome electrophotographic path.
- Research Rev B corrected OPC exposure units to µJ/cm², fixed LED shift-clock math, added exposure-to-development delay guardrails, and separated cited research grounding from novel design hypotheses.

## What changed in Rev C

Rev C turned the research corrections into engineering engines — solved geometry, checked electrostatics, and a working calibration loop — instead of guardrail prose:

- **Solved drum station map** (`openframe_printer/station_map.py`, doc 31): exact roller-clearance math places every process station around the drum. Headline: the Rev B 50 ms exposure-to-development target is geometrically impossible on the 30 mm drum package (minimum feasible ≈ 160 ms); the binding spec moves to the OPC as a measurable contrast-hold requirement (≥90% at 240 ms).
- **Electrostatic voltage ladder** (`openframe_printer/voltage_ladder.py`, doc 32): connects PCR bias → charged surface → exposure → developer window in one checked chain. It proves **Rev A as tabled cannot print** — −720 V DC on the charge roller yields a −70 to −220 V drum, not the assumed −600 V — and proposes two concrete fixes.
- **PIDC-first calibration, implemented** (`openframe_printer/pidc_model.py`, doc 33): hypothesis H1 as running code — model, noise-tolerant fitter, latent-voltage-targeted LED pulse chooser, and a synthetic rig whose kill criteria pass/fail automatically.
- **Unit-safety layer** (`openframe_printer/units.py`): every generated JSON passes a unit-plausibility lint, so the Rev B mJ/µJ bug class now fails the build instead of waiting for a reviewer.

## What changed in Rev D

Rev D found and fixed a Rev C artifact drift: Rev C's prose and CSV retired the impossible −720 V PCR bias, but the generated HV JSON and smoke test still allowed the old value. Rev D makes the fixed HV ladder executable and adds two new quantitative engines:

- **Generated HV table is now authoritative** (`openframe_printer/hv_model.py`): `out/v2_hv_bias_channels.json` exposes only `PCR_CHARGE` Option A (`A_dc_only`, −1180 V nominal) or Option B (`B_ac_dc`, −600 V DC plus 1.7 kVpp AC). The old −720 V PCR target is now a retired value and cannot pass the smoke test.
- **HV consistency gate** (`out/v2_hv_consistency.json`, doc 35): checks the generated HV rows against `out/v2_voltage_ladder.json`. If the ladder, CSV, and generated table drift apart again, the build fails.
- **H8 developer-roller probe budget** (`openframe_printer/dev_probe.py`, doc 36): turns the developer-as-electrostatic-probe idea into a signal/noise budget. A 64×64-pixel patch gives about 6.45 nA full-scale ideal signal; a realistic first test should use 128×128 patches and a real transimpedance/current-sense DEV_MON mode. Plain HV voltage readback is not assumed good enough.
- **Transfer impedance control** (`openframe_printer/transfer_model.py`, doc 37): replaces fixed transfer-voltage faith with a current-limited paper/nip impedance sniff. Normal paper impedances run at the voltage target; extreme dry/high-impedance cases are rejected or slowed instead of silently under-transferring.
- **New falsifiable hypotheses** (doc 38): developer TIA mode as a calibrator, density-aware transfer waveform shaping, and a sacrificial non-image impedance strip for low-cost paper classification.
- Focused test suite: `python3 scripts/model_tests.py` runs alongside the generated-artifact smoke test.

## What changed in Rev E

Rev D hardened the electrostatics; Rev E covers the four subsystems no revision had modeled at all — the wire protocol, the safety chain's fault tolerance, the raster screen, and the consumable mass balance:

- **OFP1 exists now** (`openframe_printer/ofp1.py`, doc 39): every revision since v1 *named* the "deterministic OFP1 protocol"; none defined it. Rev E ships the binary framing (per-frame CRC-16/CCITT, whole-page CRC, blank-line SKIP compression), a reference encoder and engine-side decoder that round-trip a page bit-exactly under arbitrary byte chunking, and proof that a flipped bit is NACKed, never printed. The transport budget is honest: a worst-case page needs 7.6 Mbit/s — 78% of the USB Full Speed bulk ceiling — so production is USB High Speed, FS is the degraded service mode.
- **Interlock single-fault analysis** (`openframe_printer/interlock_faults.py`, doc 40): exhaustively enumerates stuck-at faults with adversarial firmware. The chain as documented has **7 single-point-failure nets** — one welded cover switch, one shorted loop, or one stuck enable gate leaves HV/LED/fuser live with a door open. The Rev E dual-chain topology (logic gates plus an independent energy-path relay) survives every single fault; defeating it requires two.
- **EP-safe halftoning** (`openframe_printer/halftone.py`, doc 41): EP cannot stably develop an isolated 42 µm pixel, so the host screen is now an executable constraint. The 2×2-seeded clustered-dot screen emits zero isolated pixels at every tone; Bayer and error diffusion emit up to ~1000 per 64×64 highlight patch and are rejected with numbers, not folklore.
- **Toner mass balance and the no-DRM gauge** (`openframe_printer/toner_budget.py`, doc 42): retires a live doc/artifact contradiction — docs claimed "about 2400 pages" per 80 g while the generated math said ~4800; neither survived. The loss-adjusted model (90% transfer efficiency, 8% hopper residual) rates ~4000 pages, sizes the cartridge waste cavity the RFQ requirement implies (≈28 cm³), and derives the pixel-count gauge constant (~11 mg per million black pixels) that replaces lockout chips.
- Focused test suite: `python3 scripts/model_tests.py` now runs 48 tests alongside the generated-artifact smoke test.

## Important safety boundary

This is an engineering design package, not a certified appliance. The first physical rig must be a cold paper-motion rig. HV, fuser heat, and LED output are hardware-gated and default off in the firmware model. The package includes safety interlocks because a real printer contains mains voltage, hot surfaces, and high-voltage bias rails.

## Run the design generator

```bash
cd "$HOME/Downloads" && rm -rf openframe_printer_newbuild_v2 && unzip -o openframe_printer_newbuild_v2_research_revD.zip && cd openframe_printer_newbuild_v2 && python3 -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip && python -m openframe_printer.demo && python -m openframe_printer.design_report && python scripts/smoke_test.py && python scripts/model_tests.py
```

Generated outputs land in `out/`:

```text
out/openframe_m1_page.pbm
out/openframe_m1_job_plan.json
out/v2_design_report.md
out/v2_design_calcs.json
out/v2_exposure_summary.json
out/v2_motion_events.json
out/v2_hv_bias_channels.json
out/v2_hv_consistency.json
out/v2_fuser_summary.json
out/v2_fuser_sim.csv
out/v2_led_group_map.csv
out/v2_interlock_matrix.csv
out/v2_openframe_m1_cross_section.svg
out/v2_process_cartridge.svg
out/v2_nozzle_math.json
out/v2_ep_physics_summary.json
out/v2_station_map.json
out/v2_station_map.csv
out/v2_voltage_ladder.json
out/v2_pidc_calibration_demo.json
out/v2_dev_probe_budget.json
out/v2_transfer_impedance_plan.json
```
