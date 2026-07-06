# 27. v2 file index

Use these files as the v2/Rev G authoritative package. Historical Rev A tables are retained for traceability, but active HV, safety, raster, toner, fuser, LED-thermal, transport, motion, optical, erase, environment, emissions, and registration decisions come from the generated Rev G artifacts.

## Numeric constants

- `hardware/design_targets_revA.yaml` — original geometry and speed constants
- `openframe_printer/engine_math.py`
- `out/v2_design_calcs.json`
- `out/v2_ep_physics_summary.json`
- `out/v2_station_map.json`
- `out/v2_voltage_ladder.json`
- `out/v2_toner_mass_balance.json`
- `out/v2_toner_artifact_consistency.json`
- `out/v2_fuser_power_balance.json`
- `out/v2_led_thermal_feedforward.json`
- `out/v2_ofp1_realtime_spool.json`
- `out/v2_registration_edge_budget.json`
- `out/v2_motion_registration_budget.json`
- `out/v2_optical_mtf_budget.json`
- `out/v2_fuser_thermal_safety.json`
- `out/v2_erase_ghost_budget.json`
- `out/v2_hv_discharge_bleed.json`
- `out/v2_environment_derating.json`
- `out/v2_emissions_containment.json`

## Electronics and wiring

- `hardware/ofp_m1_revA_schematic.md` — historical original wiring sketch
- `hardware/ofp_m1_revA_connectors.csv` — historical Rev A connector table
- `hardware/ofp_m1_revD_connectors_delta.csv` — active HV/contact delta from Rev A to Rev D
- `hardware/ofp_m1_revF_interlock_delta.csv` — active Rev F physically diverse interlock-energy separator delta
- `hardware/ofp_m1_revG_transport_delta.csv` — active Rev G host/spool/clutch-start transport delta
- `hardware/ofp_m1_revG_motion_encoder_delta.csv` — active Rev G drum encoder and timestamping delta
- `hardware/ofp_m1_revG_ledbar_optical_acceptance.csv` — active Rev G LED optical acceptance delta
- `hardware/ofp_m1_revG_fuser_safety_delta.csv` — active Rev G fuser cutoff delta
- `hardware/ofp_m1_revG_process_safety_delta.csv` — active Rev G erase, HV-discharge, environment, emissions, and edge-registration delta
- `hardware/ofp_m1_revA_power_tree.csv`
- `hardware/ofp_m1_revA_hv_bias_channels.csv` — historical retired PCR table
- `hardware/ofp_m1_revB_lab_developer_bias_options.csv`
- `hardware/ofp_m1_revC_hv_bias_channels.csv` — Rev C proposal table
- `hardware/ofp_m1_revD_hv_bias_channels.csv` — active HV order table
- `hardware/ofp_m1_revD_connectors_delta.csv`
- `out/v2_hv_bias_channels.json` — generated active HV table
- `out/v2_hv_consistency.json` — generated HV artifact consistency gate
- `hardware/ofp_m1_revA_netlist.tsv`
- `hardware/ofp_m1_revA_sensor_map.csv`
- `hardware/ofp_m1_revA_motor_map.csv`
- `hardware/ofp_m1_revA_interlock_matrix.csv` — historical single-loop matrix; superseded by Rev F topology C for hazardous energy
- `hardware/interlock_chain.md` — active Rev F interlock design note
- `out/v2_interlock_fault_analysis.json` — generated independent/common-cause fault enumeration
- `out/v2_hv_discharge_bleed.json` — generated stored-charge decay and bleeder gate

## Mechanics

- `docs/17_process_cartridge_mechanics.md`
- `docs/21_paper_path_geometry_revA.md`
- `mechanical/openframe_m1_revA_chassis.scad`
- `mechanical/openframe_m1_revA_cross_section.svg`
- `mechanical/process_cartridge_revA.svg`

## Firmware and transport

- `firmware/rp2040_engine_controller/include/openframe_pins.h`
- `firmware/rp2040_engine_controller/src/main.cpp`
- `firmware/rp2040_engine_controller/README.md`
- `openframe_printer/ofp1.py`
- `out/v2_ofp1_transport_budget.json`
- `out/v2_ofp1_realtime_spool.json`

## Simulation and generated outputs

- `openframe_printer/design_report.py`
- `openframe_printer/fuser_model.py`
- `openframe_printer/fuser_power.py`
- `openframe_printer/motion_model.py`
- `openframe_printer/exposure_model.py`
- `openframe_printer/hv_model.py`
- `openframe_printer/voltage_ladder.py`
- `openframe_printer/station_map.py`
- `openframe_printer/pidc_model.py`
- `openframe_printer/dev_probe.py`
- `openframe_printer/transfer_model.py`
- `openframe_printer/halftone.py`
- `openframe_printer/toner_budget.py`
- `openframe_printer/interlock_faults.py`
- `openframe_printer/led_thermal.py`
- `openframe_printer/ofp1_realtime.py`
- `openframe_printer/motion_registration.py`
- `openframe_printer/optical_mtf.py`
- `openframe_printer/fuser_safety.py`
- `openframe_printer/erase_model.py`
- `openframe_printer/hv_discharge.py`
- `openframe_printer/environment_model.py`
- `openframe_printer/emissions_model.py`
- `openframe_printer/registration_budget.py`
- `openframe_printer/nozzle_math.py`
- `openframe_printer/ep_physics.py`
- `scripts/smoke_test.py`
- `scripts/model_tests.py`

## Future inkjet/nozzle branch

- `docs/22_nozzles_future_inkjet_rev0.md`
- `hardware/inkjet_nozzle_design_space.csv`
- `openframe_printer/nozzle_math.py`

## Research and engineering revisions

- `docs/28_research_grounding_revB.md`
- `docs/29_novel_design_hypotheses_revB.md`
- `docs/30_revB_critical_corrections.md`
- `docs/31_revC_station_map.md`
- `docs/32_revC_voltage_ladder.md`
- `docs/33_revC_pidc_calibration.md`
- `docs/34_revC_new_hypotheses.md`
- `docs/35_revD_hv_generation_consistency.md`
- `docs/36_revD_developer_probe_budget.md`
- `docs/37_revD_transfer_impedance_control.md`
- `docs/38_revD_new_hypotheses.md`
- `docs/39_revE_ofp1_protocol.md`
- `docs/40_revE_interlock_single_fault.md`
- `docs/41_revE_halftone_printability.md`
- `docs/42_revE_toner_mass_balance.md`
- `docs/43_revF_halftone_floor_correction.md`
- `docs/44_revF_interlock_common_cause.md`
- `docs/45_revF_toner_artifact_consistency.md`
- `docs/46_revF_fuser_power_balance.md`
- `docs/47_revF_led_thermal_feedforward.md`
- `docs/48_revF_new_hypotheses.md`
- `docs/49_revG_ofp1_realtime_spool.md`
- `docs/50_revG_motion_registration.md`
- `docs/51_revG_ledbar_optical_mtf.md`
- `docs/52_revG_fuser_thermal_safety.md`
- `docs/53_revG_new_hypotheses.md`
- `docs/54_revG_erase_ghost_budget.md`
- `docs/55_revG_hv_discharge_bleed.md`
- `docs/56_revG_environment_derating.md`
- `docs/57_revG_emissions_containment.md`
- `docs/58_revG_registration_edge_budget.md`
