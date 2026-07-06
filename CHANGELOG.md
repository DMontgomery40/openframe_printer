# Changelog

## Engineering Rev E

- Added `openframe_printer/ofp1.py`: the OFP1 wire protocol, referenced by name since v1 and never defined, is now a specified binary framing (CRC-16/CCITT per frame, whole-page CRC, blank-line SKIP runs) with a reference encoder and engine-side decoder. Round-trip is bit-exact under arbitrary chunking; a single flipped bit is NACKed and can never reach paper. `out/v2_ofp1_transport_budget.json` shows a worst-case page needs 7.6 Mbit/s, 78% of the USB Full Speed bulk ceiling: production transport is USB High Speed, FS is the degraded service mode.
- Added `openframe_printer/interlock_faults.py`: exhaustive stuck-at fault enumeration of the interlock chain under adversarial firmware. The documented one-switch-per-door chain has 7 single-point-failure nets that leave hazards live with a door open; the proposed dual-chain topology (logic enable gates + independent energy-path relay, two contacts per door) survives every single fault. Emits `out/v2_interlock_fault_analysis.json`.
- Added `openframe_printer/halftone.py`: EP-aware halftoning. A 2×2-seeded clustered-dot screen guarantees no sub-development-size (isolated 42 µm) feature at any tone; Bayer and Floyd-Steinberg comparators fail the isolated-pixel lint by hundreds per highlight patch. Emits `out/v2_halftone_printability.json`.
- Added `openframe_printer/toner_budget.py`: toner mass balance. Retired the unsourced "about 2400 pages" claim in `docs/25_open_consumables_spec.md` (generated math said ~4800 naive; the loss-adjusted rating is ~4000 at 90% transfer efficiency and 8% hopper residual — the same doc/artifact-drift class Rev D's HV gate catches, still live in Rev D). Sizes the waste cavity the cartridge RFQ requirement implies and derives the pixel-count no-DRM gauge constant. Emits `out/v2_toner_mass_balance.json`.
- Added docs 39–42 (OFP1 protocol, interlock fault analysis, halftone printability, toner mass balance) and NEXT.md rigs 2b (OFP1 loopback) and 3e (interlock fault-injection).
- Expanded `scripts/model_tests.py` from 28 to 48 tests; smoke test now requires the four Rev E artifacts and keeps the retired 2400-page claim out of the docs.

## Engineering Rev D

- Fixed a Rev C artifact regression: `hardware/ofp_m1_revC_hv_bias_channels.csv` retired the impossible −720 V PCR bias, but generated `out/v2_hv_bias_channels.json` still emitted the old Rev A value. Rev D moves the Rev C charging fixes into `openframe_printer/hv_model.py` and makes the generated JSON authoritative.
- Added `out/v2_hv_consistency.json`: build gate that cross-checks generated HV rows against the voltage ladder. It fails if the retired −720 V PCR value returns, if Option A drifts from −1180 V, or if Option B's 1.7 kVpp AC headroom no longer matches the ladder.
- Added `hardware/ofp_m1_revD_hv_bias_channels.csv`: concrete HV module order table with PCR Option A (`A_dc_only`, −1180 V nominal) and Option B (`B_ac_dc`, −600 V DC plus 1.7 kVpp AC), plus developer and transfer rails.
- Added `openframe_printer/dev_probe.py`: H8 developer-roller-as-probe signal budget. It computes patch capacitance, induced charge, transit time, expected nanoamp signal, step spacing, and minimum DEV_MON noise requirement. The model rejects the lazy assumption that ordinary HV voltage readback is enough.
- Added `openframe_printer/transfer_model.py`: current-limited transfer control from a pre-image paper/nip impedance sniff. It computes target current from measured impedance, clamps at safe current and voltage boundaries, and explicitly rejects/slows extreme high-impedance paper states.
- Added docs 35–38: HV artifact consistency, developer-probe budget, transfer impedance control, and Rev D hypotheses.
- Updated active HV/process-cartridge docs and RFQ text so new builds reference the Rev D HV table instead of the retired Rev A −720 V PCR target.
- Expanded `scripts/model_tests.py` from 20 to 28 tests and updated `scripts/smoke_test.py` to require the Rev D artifacts.

## Engineering Rev C

- Added `openframe_printer/station_map.py`: exact-clearance drum station solver. Found the Rev B 50 ms exposure-to-development target geometrically infeasible (minimum ≈ 160 ms on Rev A geometry); replaced it with a derived, measurable OPC contrast-hold requirement (≥90% at 240 ms). Emits `out/v2_station_map.json` / `.csv`.
- Added `openframe_printer/voltage_ladder.py`: end-to-end electrostatic ladder. Found Rev A cannot print as tabled (−720 V DC PCR yields a −70 to −220 V drum surface, not the assumed −600 V; the developer background field reverses). Added `hardware/ofp_m1_revC_hv_bias_channels.csv` with DC-only (−1180 V) and AC+DC (−600 V + ≥1.7 kVpp) charging options. Emits `out/v2_voltage_ladder.json`.
- Added `openframe_printer/pidc_model.py`: hypothesis H1 implemented — PIDC model, dependency-free fitter, latent-voltage-targeted LED pulse chooser, synthetic rig with automated kill criteria. Emits `out/v2_pidc_calibration_demo.json`.
- Added `openframe_printer/units.py`: named unit conversions plus a unit-plausibility lint run on every generated JSON artifact; the Rev B mJ/µJ bug class now fails the build.
- Added docs 31–34 (station map, voltage ladder, PIDC calibration, new hypotheses H8–H10) and `scripts/model_tests.py` (20 focused tests).
- NEXT.md rig 3 updated to the Rev C charging options; added rig 3b (PIDC coupon rig) with numeric pass/fail gates.

## Research Rev B

- Corrected OPC exposure units from mJ/cm² to µJ/cm².
- Corrected LED shift-clock calculation: 5120 bits at 20 MHz is 256 µs, so two lanes or >30 MHz single-lane is required for the 25% line-time budget.
- Added `openframe_printer/ep_physics.py` and generated `out/v2_ep_physics_summary.json`.
- Added research grounding and novel hypothesis docs: `docs/28_research_grounding_revB.md`, `docs/29_novel_design_hypotheses_revB.md`, and `docs/30_revB_critical_corrections.md`.
- Promoted exposure-to-development delay, developer sub-biases, and fuser dimensional controls from vague calibration text into explicit engineering targets.
- Added `hardware/ofp_m1_revB_lab_developer_bias_options.csv` and lab-only developer contacts in `docs/17_process_cartridge_mechanics.md`.

## v2

- Reframed package as a new printer design, not a wrapper, bridge, or modified existing printer.
- Locked OpenFrame M1 Rev A constants: 600 dpi, 12 ppm, 5120-pixel LED bar, 30 mm OPC drum, 62.0 mm/s process speed.
- Added generated design report and smoke test.
- Added Rev A connector map, power tree, sensor map, motor map, interlock matrix, HV bias table, and netlist.
- Added fuser thermal model and generated CSV.
- Added paper-path motion model and jam windows.
- Added process cartridge mechanics and open consumables spec.
- Added future inkjet/nozzle design-space file and nozzle math.
- Added firmware pin contract and safe cold-rig RP2040 skeleton.
- Cleaned packaged zip by removing `.git`, `.venv`, `.DS_Store`, `__pycache__`, and macOS resource-fork files.

## v1

- First from-scratch conceptual newbuild package with initial monochrome LED electrophotographic architecture.
