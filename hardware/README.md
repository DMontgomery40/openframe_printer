# Hardware tables

Active HV values for new work are Rev D and remain unchanged through Rev G:

- `hardware/ofp_m1_revD_hv_bias_channels.csv`
- generated `out/v2_hv_bias_channels.json`
- generated `out/v2_hv_consistency.json`

Active hazardous-energy interlock guidance is Rev F, with Rev G fuser cutoff checks added:

- `hardware/interlock_chain.md`
- `hardware/ofp_m1_revF_interlock_delta.csv`
- generated `out/v2_interlock_fault_analysis.json`

The Rev A HV, connector, and interlock CSVs are retained as historical traceability files. Do not order an HV module from the Rev A PCR value; the −720 V PCR target is retired. Do not build the Rev A single-loop interlock for a hazardous rig; Rev F topology C is the current minimum.


Active Rev G transport/motion/optical/fuser/process-safety deltas:

- `hardware/ofp_m1_revG_transport_delta.csv`
- `hardware/ofp_m1_revG_motion_encoder_delta.csv`
- `hardware/ofp_m1_revG_ledbar_optical_acceptance.csv`
- `hardware/ofp_m1_revG_fuser_safety_delta.csv`
- `hardware/ofp_m1_revG_process_safety_delta.csv`
- generated `out/v2_ofp1_realtime_spool.json`
- generated `out/v2_motion_registration_budget.json`
- generated `out/v2_optical_mtf_budget.json`
- generated `out/v2_fuser_thermal_safety.json`
- generated `out/v2_erase_ghost_budget.json`
- generated `out/v2_hv_discharge_bleed.json`
- generated `out/v2_environment_derating.json`
- generated `out/v2_emissions_containment.json`
- generated `out/v2_registration_edge_budget.json`

Do not treat OFP1 CRC correctness as permission to start paper motion; Rev G requires proven spool margin. Do not order an LED bar on pixel count alone; Rev G requires MTF/spot evidence at the OPC plane. Do not treat the interlock proof as stored-charge discharge proof; each HV node now needs a measured bleeder decay path. Do not claim full Letter edge latitude from 5120 pixels unless lateral registration is proven or printable width is reduced.
