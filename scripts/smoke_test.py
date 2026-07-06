from pathlib import Path
import csv
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

subprocess.run([sys.executable, "-m", "openframe_printer.demo"], cwd=ROOT, check=True)

required = [
    "out/openframe_m1_page.pbm",
    "out/openframe_m1_job_plan.json",
    "out/v2_design_report.md",
    "out/v2_design_calcs.json",
    "out/v2_exposure_summary.json",
    "out/v2_motion_events.json",
    "out/v2_hv_bias_channels.json",
    "out/v2_fuser_summary.json",
    "out/v2_fuser_sim.csv",
    "out/v2_led_group_map.csv",
    "out/v2_interlock_matrix.csv",
    "out/v2_openframe_m1_cross_section.svg",
    "out/v2_process_cartridge.svg",
    "out/v2_nozzle_math.json",
    "out/v2_ep_physics_summary.json",
    "out/v2_station_map.json",
    "out/v2_station_map.csv",
    "out/v2_voltage_ladder.json",
    "out/v2_pidc_calibration_demo.json",
    "out/v2_hv_consistency.json",
    "out/v2_dev_probe_budget.json",
    "out/v2_transfer_impedance_plan.json",
    "out/v2_ofp1_transport_budget.json",
    "out/v2_interlock_fault_analysis.json",
    "out/v2_halftone_printability.json",
    "out/v2_halftone_floor_gate.json",
    "out/v2_toner_mass_balance.json",
    "out/v2_toner_artifact_consistency.json",
    "out/v2_fuser_power_balance.json",
    "out/v2_led_thermal_feedforward.json",
    "out/v2_ofp1_realtime_spool.json",
    "out/v2_motion_registration_budget.json",
    "out/v2_optical_mtf_budget.json",
    "out/v2_fuser_thermal_safety.json",
    "out/v2_registration_edge_budget.json",
    "out/v2_emissions_containment.json",
    "out/v2_environment_derating.json",
    "out/v2_hv_discharge_bleed.json",
    "out/v2_erase_ghost_budget.json",
]
for rel in required:
    p = ROOT / rel
    assert p.exists(), f"missing {rel}"
    assert p.stat().st_size > 0, f"empty {rel}"

pbm = ROOT / "out/openframe_m1_page.pbm"
assert pbm.read_text(encoding="ascii").startswith("P1\n"), "PBM header invalid"

job = json.loads((ROOT / "out/openframe_m1_job_plan.json").read_text(encoding="utf-8"))
assert job["safe_defaults"]["is_donor_printer_conversion"] is False
assert job["safe_defaults"]["hv_enabled"] is False
assert job["safe_defaults"]["fuser_enabled"] is False
assert job["safe_defaults"]["led_output_enabled"] is False

calcs = json.loads((ROOT / "out/v2_design_calcs.json").read_text(encoding="utf-8"))
assert calcs["target"]["revision"] == "M1-REV-A"
assert 61.9 < calcs["process_speed_mm_s_letter"] < 62.1
assert 1464.0 < calcs["line_rate_lps_letter"] < 1465.2
assert 682.0 < calcs["line_period_us_letter"] < 684.0
assert calcs["led_pixels"] == 5120
assert calcs["led_line_payload_bytes"] == 640
assert 39.0 < calcs["drum_rpm"] < 40.0
assert 80.0 < calcs["fuser_nip_dwell_ms"] < 81.5
assert "first_prototype_prints_per_80g_toner_at_5pct" not in calcs
assert "naive_upper_bound_prints_per_80g_toner_at_5pct_ignores_transfer_and_residual_losses" in calcs
assert calcs["retired_unqualified_prints_per_80g_key_removed"] is True

exposure = json.loads((ROOT / "out/v2_exposure_summary.json").read_text(encoding="utf-8"))
assert exposure["recommended_shift_clock_mhz_revB"] == 20.0
assert exposure["recommended_data_lanes_revB"] == 2
assert 29.0 < exposure["minimum_single_lane_clock_mhz_for_25pct_line_time"] < 31.0
assert 14.0 < exposure["minimum_dual_lane_clock_mhz_for_25pct_line_time"] < 16.0
assert exposure["single_lane_fraction_of_line_period_at_20mhz"] > 0.35
assert exposure["dual_lane_fraction_of_line_period_at_20mhz"] < 0.20
assert "exposure_energy_sweep_uJ_cm2" in exposure
assert "exposure_energy_sweep_mJ_cm2" not in exposure

motion = json.loads((ROOT / "out/v2_motion_events.json").read_text(encoding="utf-8"))
events = {row["station"]: row for row in motion["events"]}
assert events["registration_nip"]["y_mm"] == 112.0
assert events["transfer_nip"]["y_mm"] == 180.0
assert motion["image_sync_to_transfer_lines"] > 980

hv = json.loads((ROOT / "out/v2_hv_bias_channels.json").read_text(encoding="utf-8"))
pcr_rows = [row for row in hv if row["name"] == "PCR_CHARGE"]
assert {row["option"] for row in pcr_rows} == {"A_dc_only", "B_ac_dc"}
assert all(row["nominal_v"] != -720.0 for row in pcr_rows)
assert next(row for row in pcr_rows if row["option"] == "A_dc_only")["nominal_v"] == -1180.0
assert next(row for row in pcr_rows if row["option"] == "B_ac_dc")["ac_component_kvpp"] == 1.7
by_name = {row["name"]: row for row in hv if row["name"] != "PCR_CHARGE"}
assert by_name["DEVELOPER_BIAS"]["nominal_v"] == -320.0
assert by_name["TRANSFER_ROLLER"]["nominal_v"] == 1600.0
assert by_name["TRANSFER_ROLLER"]["current_limit_uA"] == 500.0

fuser = json.loads((ROOT / "out/v2_fuser_summary.json").read_text(encoding="utf-8"))
assert fuser["faulted"] is False
assert fuser["first_print_enable_s"] is not None
assert fuser["max_temp_c"] < 205.0

nozzle = json.loads((ROOT / "out/v2_nozzle_math.json").read_text(encoding="utf-8"))
assert 26.0 < nozzle["droplet_diameter_um_for_target_volume"] < 27.5
assert 40.0 < nozzle["reynolds_number"] < 70.0

physics = json.loads((ROOT / "out/v2_ep_physics_summary.json").read_text(encoding="utf-8"))
assert physics["led_shift_budget"]["minimum_single_lane_clock_mhz_for_25pct_line"] > 29.0
assert physics["exposure_development_constraints"]["50ms"]["max_arc_length_mm"] < 3.2
assert physics["exposure_development_constraints"]["50ms"]["max_angular_separation_deg_for_30mm_drum"] < 12.5

with (ROOT / "out/v2_led_group_map.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 80
assert rows[0]["first_pixel"] == "0"
assert rows[-1]["last_pixel"] == "5119"

# Rev C: solved station map replaces the infeasible 50 ms guardrail.
stations = json.loads((ROOT / "out/v2_station_map.json").read_text(encoding="utf-8"))
assert stations["ring_closes"] is True
expo = stations["exposure_to_development"]
assert expo["rev_b_50ms_target_feasible"] is False
assert 100.0 < expo["min_feasible_delay_ms"] < 400.0
assert stations["derived_opc_requirement"]["latent_contrast_hold_ms"] >= expo["min_feasible_delay_ms"]

# Rev C: voltage ladder proves Rev A charging broken and both fixes viable.
ladder = json.loads((ROOT / "out/v2_voltage_ladder.json").read_text(encoding="utf-8"))
assert ladder["rev_a_as_tabled"]["verdict_broken"] is True
for rung in ladder["rev_c_option_a_dc_only"]["band"]:
    assert rung["development_contrast_ok"] and rung["fog_margin_ok"]
option_b = ladder["rev_c_option_b_ac_dc"]["rung"]
assert option_b["development_contrast_ok"] and option_b["fog_margin_ok"]
assert ladder["rev_c_option_b_ac_dc"]["pcr_ac_physics_min_kvpp"] == 1.3
assert ladder["rev_c_option_b_ac_dc"]["pcr_ac_spec_kvpp_with_headroom"] == 1.7

hv_consistency = json.loads((ROOT / "out/v2_hv_consistency.json").read_text(encoding="utf-8"))
assert hv_consistency["all_checks_pass"] is True
assert hv_consistency["checks"]["retired_rev_a_pcr_bias_absent"] is True

# Rev C: the PIDC-first calibration loop closes under rig noise.
pidc = json.loads((ROOT / "out/v2_pidc_calibration_demo.json").read_text(encoding="utf-8"))
assert pidc["kill_criteria"]["h1_loop_closes"] is True
assert pidc["pulse_choice"]["within_line_budget"] is True

with (ROOT / "hardware/ofp_m1_revD_hv_bias_channels.csv").open(newline="", encoding="utf-8") as f:
    revd_rows = list(csv.DictReader(f))
assert {r["option"] for r in revd_rows if r["channel"] == "PCR_CHARGE"} == {"A_dc_only", "B_ac_dc"}

dev_probe = json.loads((ROOT / "out/v2_dev_probe_budget.json").read_text(encoding="utf-8"))
assert dev_probe["nominal_64x64_patch"]["full_scale_ideal_current_na"] > 5.0
assert dev_probe["nominal_64x64_patch"]["h8_plain_monitor_assumption_ok"] is False
assert dev_probe["recommendation_for_0_5nA_monitor"]["chosen_patch"]["group_px"] == 128

transfer = json.loads((ROOT / "out/v2_transfer_impedance_plan.json").read_text(encoding="utf-8"))
choices = {row["case"]: row for row in transfer["choices"]}
assert choices["normal_plain_paper"]["verdict"] == "run"
assert choices["extreme_impedance_reject_or_slow"]["verdict"] == "reject_or_slow_engine_for_transfer_latitude"
assert choices["extreme_impedance_reject_or_slow"]["expected_transfer_voltage_v"] <= 2500.0

# Rev D: active docs must not keep the old Rev A PCR as an operating target.
hv_doc = (ROOT / "docs/19_hv_power_and_measurement.md").read_text(encoding="utf-8")
rfq_cart = (ROOT / "rfq/rfq_02_ep_process_cartridge.md").read_text(encoding="utf-8")
next_doc = (ROOT / "NEXT.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "| PCR charge | -720 V" not in hv_doc
assert "Primary charge roller | -720 V" not in rfq_cart
assert "charge roller reaches -720 V" not in rfq_cart
assert "ofp_m1_revC_hv_bias_channels.csv" not in next_doc
assert "78 tests" in readme

# Rev E: OFP1 transport budget must state the honest USB verdict.
ofp1 = json.loads((ROOT / "out/v2_ofp1_transport_budget.json").read_text(encoding="utf-8"))
assert ofp1["worst_case_required_mbit_s"] < ofp1["usb_fs_bulk_ceiling_mbit_s"]
assert ofp1["usb_fs_is_marginal"] is True
assert ofp1["ring_buffer_covers_hiccup"] is True

# Rev E/F: interlock chain as documented is NOT single-fault safe; Rev E's dual chain
# survives independent electrical faults, but Rev F catches the common-cause actuator gap.
faults = json.loads((ROOT / "out/v2_interlock_fault_analysis.json").read_text(encoding="utf-8"))
assert faults["topology_a_as_documented"]["verdict_single_fault_safe"] is False
assert faults["topology_b_rev_e_proposal"]["verdict_single_fault_safe"] is True
assert faults["topology_b_rev_e_proposal"]["double_fault_violation_count"] > 0
assert faults["topology_b_rev_e_with_mechanical_common_cause"]["verdict_single_fault_safe_with_common_cause"] is False
assert faults["topology_c_rev_f_diverse_energy_path"]["verdict_single_fault_safe_with_common_cause"] is True

# Rev E/F: default screen must be EP-safe, dispersed comparators must fail the lint,
# and the Rev E partial-seed floor bug must stay reproduced/fixed.
screen = json.loads((ROOT / "out/v2_halftone_printability.json").read_text(encoding="utf-8"))
assert screen["seeded_screen_ep_safe"] is True
assert screen["worst_isolated_px_error_diffusion"] > 100
assert screen["worst_isolated_px_bayer_dispersed"] > 100
floor = json.loads((ROOT / "out/v2_halftone_floor_gate.json").read_text(encoding="utf-8"))
assert floor["revE_raw_screen_bug_reproduced"] is True
assert floor["revF_screen_passes_floor_gate"] is True

# Rev E: toner yield is loss-adjusted, and the retired 2400-page doc claim stays dead.
toner = json.loads((ROOT / "out/v2_toner_mass_balance.json").read_text(encoding="utf-8"))
assert 3500.0 < toner["rated_pages_at_coverage"] < toner["naive_pages_ignoring_losses"]
assert toner["required_waste_cavity_cm3_with_margin"] > 20.0
consumables_doc = (ROOT / "docs/25_open_consumables_spec.md").read_text(encoding="utf-8")
cartridge_doc = (ROOT / "docs/17_process_cartridge_mechanics.md").read_text(encoding="utf-8")
assert "about 2400 pages" not in consumables_doc
assert "about 2400 pages" not in cartridge_doc
assert "v2_toner_mass_balance.json" in consumables_doc
assert "Loss-adjusted 80 g rating target" in cartridge_doc
toner_consistency = json.loads((ROOT / "out/v2_toner_artifact_consistency.json").read_text(encoding="utf-8"))
assert toner_consistency["all_checks_pass"] is True
assert toner_consistency["loss_adjusted_pages"] < toner_consistency["naive_upper_bound_pages"]

fuser_power = json.loads((ROOT / "out/v2_fuser_power_balance.json").read_text(encoding="utf-8"))
nominal_fuser = next(c for c in fuser_power["cases"] if c["case"] == "75gsm_plain_nominal")
assert nominal_fuser["passes_steady_margin_gate"] is False
assert nominal_fuser["required_heater_w_for_margin"] > nominal_fuser["heater_power_w"]

led_thermal = json.loads((ROOT / "out/v2_led_thermal_feedforward.json").read_text(encoding="utf-8"))
assert led_thermal["compensation_bounded"] is True
assert abs(led_thermal["worst_compensated_latent_error_v"]) < 0.1

# Rev G: correctness of frames is not enough; real-time streaming needs a larger buffer or HS.
realtime = json.loads((ROOT / "out/v2_ofp1_realtime_spool.json").read_text(encoding="utf-8"))
assert realtime["revE_pause_tolerance_ms"] < 25.0
assert realtime["required_buffer_bytes_for_100ms_pause"] > realtime["revE_32_line_ring_buffer_bytes"] * 4
rt_cases = {c["case"]: c for c in realtime["cases"]}
assert rt_cases["revE_32_line_ring_10ms_target_only"]["can_finish_streaming_without_underrun"] is False
assert rt_cases["usb_fs_75pct_worst_case_12ppm_no_margin"]["can_finish_streaming_without_underrun"] is False
assert rt_cases["usb_hs_12ppm_128KiB_ring_passes_100ms"]["can_finish_streaming_without_underrun"] is True

motion_reg = json.loads((ROOT / "out/v2_motion_registration_budget.json").read_text(encoding="utf-8"))
assert motion_reg["open_loop_cases"][1]["page_scale_error_lines"] > 30.0
assert motion_reg["encoder_options"][1]["passes_quarter_line_quantization_gate"] is False
assert motion_reg["recommended_encoder"]["passes_quarter_line_quantization_gate"] is True

optics = json.loads((ROOT / "out/v2_optical_mtf_budget.json").read_text(encoding="utf-8"))
assert 45.0 < optics["max_gaussian_spot_fwhm_um_for_mtf_gate"] < 47.0
opt_cases = {c["spot_fwhm_um"]: c for c in optics["cases"]}
assert opt_cases[45.0]["passes_revG_optical_gate"] is True
assert opt_cases[50.0]["passes_revG_optical_gate"] is False

fuser_safety = json.loads((ROOT / "out/v2_fuser_thermal_safety.json").read_text(encoding="utf-8"))
assert fuser_safety["topology_firmware_only"]["verdict_single_fault_safe"] is False
assert fuser_safety["topology_firmware_only"]["single_fault_violation_count"] == 3
assert fuser_safety["topology_revG_thermostat_plus_one_shot_fuse"]["verdict_single_fault_safe"] is True


# Rev G-plus: erase, stored HV discharge, environment, emissions, and edge-slack gates.
erase = json.loads((ROOT / "out/v2_erase_ghost_budget.json").read_text(encoding="utf-8"))
assert erase["pre_revG_as_documented"]["verdict"] == "fail_ghost_memory_gate"
assert erase["revG_requirement"]["passes_energy_window"] is True
assert 93.0 < erase["ghost_test_pattern"]["predicted_repeat_distance_mm"] < 95.0

hv_bleed = json.loads((ROOT / "out/v2_hv_discharge_bleed.json").read_text(encoding="utf-8"))
assert hv_bleed["counterexample_no_bleeder"]["verdict"] == "fail_no_guaranteed_touch_safe_decay"
assert hv_bleed["all_nodes_pass_normal_60v"] is True
assert hv_bleed["all_nodes_pass_single_fault_120v"] is True

env = json.loads((ROOT / "out/v2_environment_derating.json").read_text(encoding="utf-8"))
assert env["humid_plain_requires_calibration"] is True
assert env["film_offset_v"] == 500.0
assert next(c for c in env["cases"] if c["name"] == "humid_80rh_plain")["charge_factor_vs_50rh"] < 0.86

emissions = json.loads((ROOT / "out/v2_emissions_containment.json").read_text(encoding="utf-8"))
assert emissions["fan_filter_only_is_not_enough_for_high_emitter"] is True
assert emissions["output_tray_capture_changes_verdict"] is True

edge = json.loads((ROOT / "out/v2_registration_edge_budget.json").read_text(encoding="utf-8"))
assert edge["current_5120_bar"]["passes_1mm_each_side_slack_goal"] is False
assert edge["recommended_revG_LED_or_margins"]["proposed_led_pixels"] == 5184
assert edge["old_test_plan_plus_minus_1mm"]["error_lines"] > 23.0

print("smoke_test: OK")
