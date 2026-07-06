# Changelog

## Engineering Rev G

- Added `openframe_printer/ofp1_realtime.py` and `out/v2_ofp1_realtime_spool.json`: Rev E's OFP1 framing was byte-correct, but the 32-line ring only tolerates ~21.9 ms of host silence. Rev G gates clutch start on decoded-buffer margin and proves USB FS at 75% of theoretical bulk ceiling cannot sustain 12 ppm worst-case pages.
- Added `openframe_printer/motion_registration.py` and `out/v2_motion_registration_budget.json`: open-loop speed constants are not line placement. A 0.5% process-speed error stretches Letter by 33 lines; Rev G requires encoder-slaved LED line timing and timestamped registration edges.
- Added `openframe_printer/optical_mtf.py` and `out/v2_optical_mtf_budget.json`: LED emitter count and shift timing do not prove 600 dpi latent-image contrast. Rev G adds a supplier MTF/spot-size gate: MTF >= 0.35 at 12 lp/mm or spot FWHM <= 45 µm with <=15% one-pixel crosstalk.
- Added `openframe_printer/fuser_safety.py` and `out/v2_fuser_thermal_safety.json`: Rev F's fuser power balance was not a runaway proof. Firmware-only heat control has three single-fault runaway paths; independent thermostat plus one-shot thermal fuse has zero modeled single-fault violations.
- Added `openframe_printer/erase_model.py` and `out/v2_erase_ghost_budget.json`: the old process stack had no explicit post-cleaning erase/quench station. Rev G fails that condition, sizes a bounded erase dose, and emits the one-circumference ghost-repeat target for scanner validation.
- Added `openframe_printer/hv_discharge.py` and `out/v2_hv_discharge_bleed.json`: interlocks remove enables but do not guarantee HV output capacitance decays. Rev G adds redundant bleeder sizing and normal/single-fault discharge gates.
- Added `openframe_printer/environment_model.py` and `out/v2_environment_derating.json`: humidity and media are now process variables. 80% RH plain paper holds quality printing for PIDC/developer/transfer calibration instead of silently using nominal settings.
- Added `openframe_printer/emissions_model.py` and `out/v2_emissions_containment.json`: high-emitter fan-filter-only containment fails the modeled gate; source plus output-tray capture is required before bench qualification.
- Added `openframe_printer/registration_budget.py` and `out/v2_registration_edge_budget.json`: 5120 active pixels provide only 0.373 mm per-side Letter slack; Rev G recommends 5184 pixels or a reduced printable width / tighter registration proof.
- Added docs 49-58 and Rev G hardware delta CSVs for transport, drum encoder, LED optical acceptance, fuser safety, erase/HV/environment/emissions, and edge registration.
- Expanded `scripts/model_tests.py` from 57 to 78 tests; smoke test now requires the nine Rev G artifacts.

## Engineering Rev F

- Added `out/v2_halftone_floor_gate.json` and upgraded `openframe_printer/halftone.py`: Rev E's raw 2×2-seeded screen still emitted one-pixel partial seeds below the declared 4/64 highlight floor. Rev F clips sub-floor tones and suppresses sub-2×2 connected components.
- Extended `openframe_printer/interlock_faults.py`: Rev E's dual-chain topology remains safe for independent electrical stuck-at faults, but fails a shared door-actuator/common-cause fault. Rev F adds topology C with a physically diverse energy-path separator and tests it.
- Added `out/v2_toner_artifact_consistency.json`: the unqualified `first_prototype_prints_per_80g_toner_at_5pct` key is removed from base design calcs; the ~4820-page figure survives only as an explicitly labeled naive upper bound.
- Added `openframe_printer/fuser_power.py` and `out/v2_fuser_power_balance.json`: continuous paper/moisture/toner load balance shows the existing 800 W / 0.235 °C/W fuser assumptions do not support a 10% steady reserve at 12 ppm nominal media.
- Added `openframe_printer/led_thermal.py` and `out/v2_led_thermal_feedforward.json`: H9 payload-derived LED thermal droop feed-forward now emits bounded per-group pulse compensation.
- Added docs 43-48 and expanded `scripts/model_tests.py` from 48 to 57 tests.

## Engineering Rev E

- Added `openframe_printer/ofp1.py`: the OFP1 wire protocol, referenced by name since v1 and never defined, is now a specified binary framing (CRC-16/CCITT per frame, whole-page CRC, blank-line SKIP runs) with a reference encoder and engine-side decoder. Round-trip is bit-exact under arbitrary chunking; a single flipped bit is NACKed and can never reach paper. `out/v2_ofp1_transport_budget.json` shows a worst-case page needs 7.6 Mbit/s, 78% of the USB Full Speed bulk ceiling: production transport is USB High Speed, FS is the degraded service mode.
- Added `openframe_printer/interlock_faults.py`: exhaustive stuck-at fault enumeration of the interlock chain under adversarial firmware. The documented one-switch-per-door chain has 7 single-point-failure nets that leave hazards live with a door open; the Rev E dual-chain topology survives the independent electrical stuck-at model, but Rev F later expands the model to include shared mechanical actuator faults. Emits `out/v2_interlock_fault_analysis.json`.
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
