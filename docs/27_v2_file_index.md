# 27. v2 file index

Use these files as the v2/Rev D authoritative package. Historical Rev A tables are retained for traceability, but active HV and electrophotographic calibration values come from the generated Rev D artifacts.

## Numeric constants

- `hardware/design_targets_revA.yaml` — original geometry and speed constants
- `openframe_printer/engine_math.py`
- `out/v2_design_calcs.json`
- `out/v2_ep_physics_summary.json`
- `out/v2_station_map.json`
- `out/v2_voltage_ladder.json`

## Electronics and wiring

- `hardware/ofp_m1_revA_schematic.md` — historical original wiring sketch
- `hardware/ofp_m1_revA_connectors.csv` — historical Rev A connector table
- `hardware/ofp_m1_revD_connectors_delta.csv` — active HV/contact delta from Rev A to Rev D
- `hardware/ofp_m1_revA_power_tree.csv`
- `hardware/ofp_m1_revA_hv_bias_channels.csv` — historical retired PCR table
- `hardware/ofp_m1_revB_lab_developer_bias_options.csv`
- `hardware/ofp_m1_revC_hv_bias_channels.csv` — Rev C proposal table
- `hardware/ofp_m1_revD_hv_bias_channels.csv` — active Rev D HV order table
- `out/v2_hv_bias_channels.json` — generated active HV table
- `out/v2_hv_consistency.json` — generated HV artifact consistency gate
- `hardware/ofp_m1_revA_netlist.tsv`
- `hardware/ofp_m1_revA_sensor_map.csv`
- `hardware/ofp_m1_revA_motor_map.csv`
- `hardware/ofp_m1_revA_interlock_matrix.csv`

## Mechanics

- `docs/17_process_cartridge_mechanics.md`
- `docs/21_paper_path_geometry_revA.md`
- `mechanical/openframe_m1_revA_chassis.scad`
- `mechanical/openframe_m1_revA_cross_section.svg`
- `mechanical/process_cartridge_revA.svg`

## Firmware

- `firmware/rp2040_engine_controller/include/openframe_pins.h`
- `firmware/rp2040_engine_controller/src/main.cpp`
- `firmware/rp2040_engine_controller/README.md`

## Simulation and generated outputs

- `openframe_printer/design_report.py`
- `openframe_printer/fuser_model.py`
- `openframe_printer/motion_model.py`
- `openframe_printer/exposure_model.py`
- `openframe_printer/hv_model.py`
- `openframe_printer/voltage_ladder.py`
- `openframe_printer/station_map.py`
- `openframe_printer/pidc_model.py`
- `openframe_printer/dev_probe.py`
- `openframe_printer/transfer_model.py`
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
