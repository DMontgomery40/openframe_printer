"""Focused unit tests for the Rev C/D engineering engines.

Run: python3 scripts/model_tests.py
Stdlib unittest only, matching the package's zero-dependency rule.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openframe_printer.engine_math import EngineTargets, design_calcs, process_speed_mm_s  # noqa: E402
from openframe_printer.dev_probe import developer_probe_budget, recommended_patch_for_monitor_noise  # noqa: E402
from openframe_printer.transfer_model import choose_transfer_current, transfer_impedance_plan  # noqa: E402
from openframe_printer.hv_model import hv_table, hv_consistency_summary  # noqa: E402
from openframe_printer.pidc_model import (  # noqa: E402
    PidcModel,
    choose_pulse_width,
    fit_pidc,
    model_from_discharge_requirement,
    synthetic_rig_demo,
)
from openframe_printer.station_map import (  # noqa: E402
    roller_pair_min_separation_deg,
    solve_station_map,
)
from openframe_printer.units import (  # noqa: E402
    lint_artifact,
    mj_cm2_to_uj_cm2,
    mw_cm2_to_uj_cm2_per_us,
)
from openframe_printer.voltage_ladder import (  # noqa: E402
    dc_bias_for_surface_potential_v,
    dc_roller_surface_potential_v,
    evaluate_ladder,
    ladder_summary,
)
from openframe_printer.ofp1 import (  # noqa: E402
    EngineDecoder,
    crc16_ccitt,
    encode_page,
    transport_budget,
)
from openframe_printer.interlock_faults import (  # noqa: E402
    eval_topology_a,
    eval_topology_b,
    eval_topology_c,
    interlock_fault_summary,
)
from openframe_printer.halftone import (  # noqa: E402
    bayer_matrix,
    clustered_matrix,
    ep_safe_clustered_halftone,
    feature_metrics,
    floyd_steinberg,
    halftone_floor_gate,
    isolated_black_pixels,
    printability_summary,
    screen_halftone,
)
from openframe_printer.toner_budget import (  # noqa: E402
    TonerAssumptions,
    toner_artifact_consistency,
    toner_mass_balance,
)
from openframe_printer.fuser_power import fuser_power_summary, paper_load_case  # noqa: E402
from openframe_printer.led_thermal import led_thermal_summary, simulate_led_thermal_case  # noqa: E402
from openframe_printer.ofp1_realtime import realtime_spool_summary, max_ppm_for_host_utilization  # noqa: E402
from openframe_printer.motion_registration import (  # noqa: E402
    EncoderSpec,
    encoder_resolution,
    motion_registration_summary,
    open_loop_scale_error,
    sensor_timestamp_error,
)
from openframe_printer.optical_mtf import optical_case, optical_mtf_summary  # noqa: E402
from openframe_printer.fuser_safety import eval_fuser_topology, fuser_safety_summary, FuserSafetyTopology  # noqa: E402
from openframe_printer.erase_model import erase_summary, required_erase_energy_uj_cm2, drum_rotation_period_s  # noqa: E402
from openframe_printer.hv_discharge import HVNode, evaluate_node, hv_discharge_summary, no_bleed_counterexample  # noqa: E402
from openframe_printer.environment_model import environment_summary, toner_q_over_m_uc_g, evaluate_environment, EnvironmentCase  # noqa: E402
from openframe_printer.emissions_model import EmissionCase, evaluate_emission_case, emissions_summary  # noqa: E402
from openframe_printer.registration_budget import registration_summary, minimum_pixels_for_lateral_slack, round_up_to_byte_aligned_pixels  # noqa: E402


class HvArtifactTests(unittest.TestCase):
    def test_generated_hv_table_retires_rev_a_pcr_bias(self) -> None:
        rows = hv_table()
        pcr_rows = [row for row in rows if row["name"] == "PCR_CHARGE"]
        self.assertEqual({row["option"] for row in pcr_rows}, {"A_dc_only", "B_ac_dc"})
        self.assertNotIn(-720.0, {row["nominal_v"] for row in pcr_rows})
        self.assertEqual(next(row for row in pcr_rows if row["option"] == "A_dc_only")["nominal_v"], -1180.0)
        self.assertEqual(next(row for row in pcr_rows if row["option"] == "B_ac_dc")["ac_component_kvpp"], 1.7)

    def test_hv_table_matches_voltage_ladder(self) -> None:
        summary = hv_consistency_summary(ladder_summary())
        self.assertTrue(summary["all_checks_pass"], summary)


class UnitsTests(unittest.TestCase):
    def test_conversions_are_inverse_consistent(self) -> None:
        self.assertAlmostEqual(mj_cm2_to_uj_cm2(0.00045), 0.45)
        self.assertAlmostEqual(mw_cm2_to_uj_cm2_per_us(15.0), 0.015)

    def test_lint_catches_the_rev_b_bug_shape(self) -> None:
        # 0.45 is a sane uJ/cm^2 exposure and an absurd mJ/cm^2 one.
        self.assertTrue(lint_artifact({"exposure_mj_cm2": 0.45}))
        self.assertFalse(lint_artifact({"exposure_uj_cm2": 0.45}))

    def test_lint_walks_nested_structures_and_allows_zero(self) -> None:
        nested = {"a": [{"y_mm": 0.0}, {"y_mm": 112.0}], "b": {"pulse_us": 34.0}}
        self.assertFalse(lint_artifact(nested))
        nested["a"].append({"y_mm": 999999.0})
        self.assertTrue(lint_artifact(nested))

    def test_lint_ignores_composite_per_units(self) -> None:
        self.assertFalse(lint_artifact({"heat_capacity_j_per_c": 460.0}))


class StationMapTests(unittest.TestCase):
    def test_roller_pair_separation_matches_closed_form_symmetric_case(self) -> None:
        # Two equal rollers r on drum R with zero clearance:
        # cos(theta) = 1 - (2r)^2 / (2 (R+r)^2)
        drum_r, roller_r = 15.0, 8.0
        got = roller_pair_min_separation_deg(drum_r, roller_r, roller_r, 0.0)
        expected = math.degrees(
            math.acos(1.0 - (2.0 * roller_r) ** 2 / (2.0 * (drum_r + roller_r) ** 2))
        )
        self.assertAlmostEqual(got, expected, places=9)

    def test_ring_closes_and_gaps_meet_minimums(self) -> None:
        solution = solve_station_map()
        self.assertTrue(solution["ring_closes"])
        for gap in solution["gaps"]:
            self.assertGreaterEqual(
                gap["actual_separation_deg"] + 1e-9, gap["min_separation_deg"]
            )
        total = sum(g["actual_separation_deg"] for g in solution["gaps"])
        self.assertAlmostEqual(total, 360.0, places=6)

    def test_rev_b_50ms_target_is_infeasible_on_rev_a_geometry(self) -> None:
        solution = solve_station_map()
        expo = solution["exposure_to_development"]
        self.assertFalse(expo["rev_b_50ms_target_feasible"])
        self.assertGreater(expo["min_feasible_delay_ms"], 100.0)

    def test_delays_are_consistent_with_process_speed(self) -> None:
        t = EngineTargets()
        solution = solve_station_map(t)
        speed = process_speed_mm_s(t)
        for gap in solution["gaps"]:
            self.assertAlmostEqual(
                gap["delay_ms"], gap["arc_mm"] / speed * 1000.0, delta=0.06
            )


class PidcTests(unittest.TestCase):
    def test_model_round_trips_potential_and_exposure(self) -> None:
        model = model_from_discharge_requirement(0.45)
        self.assertAlmostEqual(model.surface_potential_v(0.45), -100.0, places=6)
        for target in (-500.0, -300.0, -100.0, -70.0):
            energy = model.exposure_for_potential_uj_cm2(target)
            self.assertAlmostEqual(model.surface_potential_v(energy), target, places=6)

    def test_unreachable_targets_raise(self) -> None:
        model = model_from_discharge_requirement(0.45)
        with self.assertRaises(ValueError):
            model.exposure_for_potential_uj_cm2(-40.0)  # beyond residual

    def test_fit_recovers_noise_free_model_exactly(self) -> None:
        truth = PidcModel(v_charge_v=-600.0, v_residual_v=-80.0, e_char_uj_cm2=0.22)
        points = [(e / 100.0, truth.surface_potential_v(e / 100.0)) for e in range(10, 101, 10)]
        fitted = fit_pidc(points, v_charge_v=-600.0)
        self.assertLess(abs(fitted.v_residual_v - truth.v_residual_v), 1.0)
        self.assertLess(abs(fitted.e_char_uj_cm2 - truth.e_char_uj_cm2), 0.005)

    def test_pulse_choice_energy_math(self) -> None:
        model = model_from_discharge_requirement(0.45)
        pulse = choose_pulse_width(model, -100.0, led_irradiance_mw_cm2=15.0, line_period_us=682.8)
        self.assertAlmostEqual(pulse.exposure_needed_uj_cm2, 0.45, places=3)
        self.assertAlmostEqual(pulse.pulse_width_us, 0.45 / 0.015, delta=0.05)
        self.assertTrue(pulse.within_line_budget)

    def test_synthetic_rig_demo_is_deterministic_and_closes(self) -> None:
        a = synthetic_rig_demo()
        b = synthetic_rig_demo()
        self.assertEqual(a["fitted_model"], b["fitted_model"])
        self.assertTrue(a["kill_criteria"]["h1_loop_closes"])

    def test_synthetic_rig_fails_honestly_under_hopeless_noise(self) -> None:
        result = synthetic_rig_demo(probe_noise_v=250.0)
        self.assertFalse(result["kill_criteria"]["prediction_ok"])


class VoltageLadderTests(unittest.TestCase):
    def test_dc_charging_threshold_behavior(self) -> None:
        self.assertEqual(dc_roller_surface_potential_v(-500.0, 560.0), 0.0)
        self.assertAlmostEqual(dc_roller_surface_potential_v(-720.0, 560.0), -160.0)
        self.assertAlmostEqual(dc_roller_surface_potential_v(-1180.0, 560.0), -620.0)

    def test_bias_inversion_round_trips(self) -> None:
        for target in (-400.0, -600.0, -800.0):
            bias = dc_bias_for_surface_potential_v(target)
            self.assertAlmostEqual(dc_roller_surface_potential_v(bias), target)

    def test_rev_a_is_broken_across_full_threshold_band(self) -> None:
        summary = ladder_summary()
        self.assertTrue(summary["rev_a_as_tabled"]["verdict_broken"])
        for rung in summary["rev_a_as_tabled"]["band"]:
            self.assertFalse(rung["field_orientation_ok"])

    def test_rev_c_options_both_print_across_threshold_band(self) -> None:
        summary = ladder_summary()
        for rung in summary["rev_c_option_a_dc_only"]["band"]:
            self.assertTrue(rung["development_contrast_ok"], rung)
            self.assertTrue(rung["fog_margin_ok"], rung)
        b_option = summary["rev_c_option_b_ac_dc"]
        b = b_option["rung"]
        self.assertTrue(b["development_contrast_ok"] and b["fog_margin_ok"])
        self.assertEqual(b_option["pcr_ac_physics_min_kvpp"], 1.3)
        self.assertEqual(b_option["pcr_ac_spec_kvpp_with_headroom"], 1.7)

    def test_developer_window_holds_across_opc_sensitivity_band(self) -> None:
        summary = ladder_summary()
        for rung in summary["developer_window_across_opc_sensitivity_band"]:
            self.assertTrue(rung["development_contrast_ok"], rung)
            self.assertTrue(rung["fog_margin_ok"], rung)

    def test_ladder_flags_reversed_field_directly(self) -> None:
        rung = evaluate_ladder(pcr_applied_v=-720.0, developer_bias_v=-320.0, exposure_uj_cm2=0.45)
        self.assertFalse(rung.field_orientation_ok)
        self.assertGreater(rung.fog_margin_v, 0.0)  # wrong sign = fog


class DeveloperProbeTests(unittest.TestCase):
    def test_64_square_patch_quantifies_h8_signal(self) -> None:
        budget = developer_probe_budget(group_px=64)
        self.assertGreater(budget.full_scale_ideal_current_na, 5.0)
        self.assertLess(budget.required_monitor_noise_na_rms_for_3sigma_steps, 0.5)
        self.assertFalse(budget.h8_plain_monitor_assumption_ok)

    def test_square_patch_signal_scales_with_width(self) -> None:
        b64 = developer_probe_budget(group_px=64)
        b128 = developer_probe_budget(group_px=128)
        ratio = b128.full_scale_ideal_current_na / b64.full_scale_ideal_current_na
        self.assertAlmostEqual(ratio, 2.0, delta=0.03)

    def test_recommended_patch_for_half_na_monitor(self) -> None:
        rec = recommended_patch_for_monitor_noise(0.5)
        self.assertEqual(rec["chosen_patch"]["group_px"], 128)
        self.assertGreaterEqual(
            rec["chosen_patch"]["eight_step_current_spacing_na"],
            rec["required_adjacent_step_spacing_na"],
        )


    def test_base_design_calcs_no_longer_publish_unqualified_4800_page_yield(self) -> None:
        calcs = design_calcs()
        self.assertNotIn("first_prototype_prints_per_80g_toner_at_5pct", calcs)
        self.assertIn(
            "naive_upper_bound_prints_per_80g_toner_at_5pct_ignores_transfer_and_residual_losses",
            calcs,
        )
        consistency = toner_artifact_consistency()
        self.assertTrue(consistency["all_checks_pass"], consistency)
        self.assertLess(consistency["loss_adjusted_pages"], consistency["naive_upper_bound_pages"])



class TransferControlTests(unittest.TestCase):
    def test_transfer_current_uses_impedance_to_hold_target_voltage(self) -> None:
        choice = choose_transfer_current(30.0, case="normal")
        self.assertEqual(choice.verdict, "run")
        self.assertAlmostEqual(choice.expected_transfer_voltage_v, 1600.0, delta=0.2)
        self.assertAlmostEqual(choice.chosen_transfer_current_uA, 53.333, delta=0.002)

    def test_transfer_control_voltage_limits_extreme_impedance(self) -> None:
        choice = choose_transfer_current(800.0, case="extreme")
        self.assertEqual(choice.verdict, "reject_or_slow_engine_for_transfer_latitude")
        self.assertLessEqual(choice.expected_transfer_voltage_v, 2500.0)
        self.assertFalse(choice.current_floor_met)

    def test_transfer_plan_contains_reject_gate(self) -> None:
        plan = transfer_impedance_plan()
        choices = {row["case"]: row for row in plan["choices"]}
        self.assertEqual(choices["extreme_impedance_reject_or_slow"]["verdict"], "reject_or_slow_engine_for_transfer_latitude")


def _test_page(width_px: int = 5120, lines: int = 200, blank_every: int = 3) -> list[bytes]:
    """Deterministic page: pseudo-random rows with interleaved blank runs."""
    row_len = (width_px + 7) // 8
    rows = []
    state = 0x1234
    for i in range(lines):
        if i % blank_every == 0:
            rows.append(bytes(row_len))
            continue
        row = bytearray()
        for _ in range(row_len):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            row.append(state & 0xFF)
        rows.append(bytes(row))
    return rows


class Ofp1Tests(unittest.TestCase):
    def test_round_trip_is_bit_exact(self) -> None:
        rows = _test_page()
        frames = encode_page(rows, dpi=600, width_px=5120)
        decoder = EngineDecoder()
        for frame in frames:
            decoder.feed(frame)
        result = decoder.result()
        self.assertTrue(result.complete, result.error)
        self.assertEqual(result.rows, rows)
        self.assertEqual(result.nacks, [])

    def test_round_trip_survives_arbitrary_chunking(self) -> None:
        rows = _test_page(lines=60)
        stream = b"".join(encode_page(rows, dpi=600, width_px=5120))
        decoder = EngineDecoder()
        for i in range(0, len(stream), 7):  # deliberately misaligned chunks
            decoder.feed(stream[i:i + 7])
        result = decoder.result()
        self.assertTrue(result.complete, result.error)
        self.assertEqual(result.rows, rows)

    def test_blank_lines_travel_as_skips_not_payload(self) -> None:
        rows = [bytes(640)] * 100
        frames = encode_page(rows, dpi=600, width_px=5120)
        self.assertEqual(len(frames), 3)  # JOB_START, one SKIP, JOB_END
        self.assertLess(sum(len(f) for f in frames), 100)

    def test_single_bit_corruption_is_caught_never_printed(self) -> None:
        rows = _test_page(lines=30)
        frames = encode_page(rows, dpi=600, width_px=5120)
        payload_frame = bytearray(frames[2])
        payload_frame[20] ^= 0x01  # flip one raster bit mid-payload
        decoder = EngineDecoder()
        decoder.feed(frames[0] + frames[1] + bytes(payload_frame))
        for frame in frames[3:]:
            decoder.feed(frame)
        result = decoder.result()
        self.assertFalse(result.complete)  # dropped line -> coverage/order fault
        self.assertTrue(result.nacks)
        self.assertNotEqual(result.rows, rows)  # and it never fabricated the page

    def test_crc16_known_vector(self) -> None:
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)  # CCITT-FALSE check value

    def test_budget_says_fs_is_marginal_not_impossible(self) -> None:
        budget = transport_budget()
        self.assertLess(budget["worst_case_required_mbit_s"], budget["usb_fs_bulk_ceiling_mbit_s"])
        self.assertTrue(budget["usb_fs_is_marginal"])
        self.assertTrue(budget["ring_buffer_covers_hiccup"])


class InterlockFaultTests(unittest.TestCase):
    def test_no_fault_no_hazard_with_any_door_open(self) -> None:
        for topology in (eval_topology_a, eval_topology_b):
            for door in ("main_cover", "rear_door", "service_panel"):
                doors = {d: d != door for d in ("main_cover", "rear_door", "service_panel")}
                self.assertFalse(any(topology(doors, {}).values()))

    def test_documented_topology_has_single_point_failures(self) -> None:
        summary = interlock_fault_summary()
        a = summary["topology_a_as_documented"]
        self.assertFalse(a["verdict_single_fault_safe"])
        self.assertIn("loop:stuck_1", a["single_point_failure_nets"])
        self.assertIn("sw_main_cover:stuck_closed", a["single_point_failure_nets"])

    def test_rev_e_topology_survives_independent_electrical_faults(self) -> None:
        summary = interlock_fault_summary()
        b = summary["topology_b_rev_e_proposal"]
        self.assertTrue(b["verdict_single_fault_safe"])
        self.assertEqual(b["single_fault_violation_count"], 0)
        self.assertGreater(b["double_fault_violation_count"], 0)

    def test_welded_contact_plus_open_door_is_the_canonical_defeat(self) -> None:
        doors = {"main_cover": False, "rear_door": True, "service_panel": True}
        live_a = eval_topology_a(doors, {"sw_main_cover": "stuck_closed"})
        self.assertTrue(all(live_a.values()))
        live_b = eval_topology_b(doors, {"sw_main_cover_a": "stuck_closed"})
        self.assertFalse(any(live_b.values()))


class RevFInterlockCommonCauseTests(unittest.TestCase):
    def test_rev_e_dual_chain_fails_shared_door_actuator_fault(self) -> None:
        doors = {"main_cover": False, "rear_door": True, "service_panel": True}
        live = eval_topology_b(doors, {"door_main_cover_common_actuator": "stuck_closed_both_chains"})
        self.assertTrue(any(live.values()))
        summary = interlock_fault_summary()
        b = summary["topology_b_rev_e_with_mechanical_common_cause"]
        self.assertFalse(b["verdict_single_fault_safe_with_common_cause"])
        self.assertIn(
            "door_main_cover_common_actuator:stuck_closed_both_chains",
            b["single_point_failure_nets"],
        )

    def test_rev_f_diverse_energy_path_survives_same_fault(self) -> None:
        doors = {"main_cover": False, "rear_door": True, "service_panel": True}
        live = eval_topology_c(doors, {"door_main_cover_common_actuator": "stuck_closed_both_chains"})
        self.assertFalse(any(live.values()))
        c = interlock_fault_summary()["topology_c_rev_f_diverse_energy_path"]
        self.assertTrue(c["verdict_single_fault_safe_with_common_cause"])
        self.assertEqual(c["single_fault_violation_count"], 0)



class HalftoneTests(unittest.TestCase):
    def test_seeded_screen_never_emits_isolated_pixels(self) -> None:
        summary = printability_summary()
        self.assertTrue(summary["seeded_screen_ep_safe"])
        self.assertEqual(summary["worst_isolated_px_seeded_screen"], 0)

    def test_dispersed_methods_fail_ep_lint_in_highlights(self) -> None:
        summary = printability_summary()
        self.assertGreater(summary["worst_isolated_px_bayer_dispersed"], 100)
        self.assertGreater(summary["worst_isolated_px_error_diffusion"], 100)

    def test_screen_tone_is_monotonic_in_gray_level(self) -> None:
        matrix = clustered_matrix()
        previous = -1
        for level in [i / 20.0 for i in range(21)]:
            patch = [[level] * 16 for _ in range(16)]
            black = sum(map(sum, screen_halftone(patch, matrix)))
            self.assertGreaterEqual(black, previous)
            previous = black

    def test_error_diffusion_preserves_mean_tone(self) -> None:
        patch = [[0.25] * 64 for _ in range(64)]
        out = floyd_steinberg(patch)
        mean = sum(map(sum, out)) / (64 * 64)
        self.assertAlmostEqual(mean, 0.25, delta=0.02)

    def test_bayer_really_is_dispersed(self) -> None:
        # Sanity that the comparator is honest: at the 2-pixel tone level the
        # Bayer cell's two lit pixels are far apart, the clustered cell's touch.
        patch = [[2.5 / 64.0] * 8 for _ in range(8)]
        self.assertGreater(isolated_black_pixels(screen_halftone(patch, bayer_matrix())), 0)
        self.assertEqual(isolated_black_pixels(screen_halftone(patch, clustered_matrix())), 0)


    def test_rev_e_raw_screen_has_subfloor_partial_seed_bug(self) -> None:
        patch = [[0.001] * 8 for _ in range(8)]
        raw = screen_halftone(patch, clustered_matrix())
        metrics = feature_metrics(raw)
        self.assertGreater(metrics["isolated_black_pixels"], 0)
        self.assertGreater(metrics["sub_min_cluster_components"], 0)
        gate = halftone_floor_gate()
        self.assertTrue(gate["revE_raw_screen_bug_reproduced"])

    def test_rev_f_safe_screen_clips_subfloor_and_requires_2x2(self) -> None:
        matrix = clustered_matrix()
        for level in (0.001, 0.01, 1.0 / 64.0, 0.03, 0.05):
            safe = ep_safe_clustered_halftone([[level] * 64 for _ in range(64)], matrix)
            metrics = feature_metrics(safe)
            self.assertEqual(metrics["black_pixels"], 0)
            self.assertTrue(metrics["ep_safe"])
        at_floor = ep_safe_clustered_halftone([[4.0 / 64.0] * 64 for _ in range(64)], matrix)
        metrics = feature_metrics(at_floor)
        self.assertGreater(metrics["black_pixels"], 0)
        self.assertTrue(metrics["ep_safe"])



class TonerBudgetTests(unittest.TestCase):
    def test_losses_cost_double_digit_yield_percentage(self) -> None:
        balance = toner_mass_balance()
        self.assertLess(balance["rated_pages_at_coverage"], balance["naive_pages_ignoring_losses"])
        self.assertAlmostEqual(
            balance["rated_over_naive_ratio"],
            (1.0 - 0.08) * 0.9,
            places=6,
        )

    def test_mass_is_conserved_per_page(self) -> None:
        balance = toner_mass_balance()
        self.assertAlmostEqual(
            balance["developed_per_page_mg_at_coverage"],
            balance["on_paper_per_page_mg_at_coverage"] + balance["waste_per_page_mg_at_coverage"],
            places=9,
        )

    def test_waste_cavity_requirement_scales_with_transfer_loss(self) -> None:
        worse = toner_mass_balance(assume=TonerAssumptions(transfer_efficiency=0.80))
        base = toner_mass_balance()
        self.assertGreater(
            worse["required_waste_cavity_cm3_with_margin"],
            base["required_waste_cavity_cm3_with_margin"],
        )

    def test_pixel_gauge_constant_matches_laydown_model(self) -> None:
        balance = toner_mass_balance()
        # 1 Mpx of black at 600 dpi is 17.92 cm^2; developed mass = area * DMA / eta.
        expected = 17.92111 * 0.55 / 0.90
        self.assertAlmostEqual(
            balance["gauge"]["developed_mg_per_megapixel_black"], expected, delta=0.01
        )

    def test_retired_2400_page_claim_stays_retired(self) -> None:
        balance = toner_mass_balance()
        self.assertGreater(balance["rated_pages_at_coverage"], 3500.0)
        self.assertEqual(balance["doc_consistency"]["retired_claim"], "about 2400 pages")


class FuserPowerBalanceTests(unittest.TestCase):
    def test_warmup_model_is_not_a_12ppm_throughput_proof(self) -> None:
        summary = fuser_power_summary()
        nominal = next(c for c in summary["cases"] if c["case"] == "75gsm_plain_nominal")
        self.assertFalse(nominal["passes_steady_margin_gate"])
        self.assertGreater(nominal["load_w"]["total_media_load"], 100.0)
        self.assertLess(nominal["remaining_margin_w"], nominal["required_margin_w"])
        self.assertGreater(nominal["required_heater_w_for_margin"], nominal["heater_power_w"])

    def test_damp_heavy_media_requires_power_insulation_or_speed_limit(self) -> None:
        summary = fuser_power_summary()
        heavy = next(c for c in summary["cases"] if c["case"] == "90gsm_damp_heavy")
        self.assertEqual(heavy["verdict"], "insulate_raise_power_or_slow_media")
        self.assertLess(heavy["slow_to_ppm_for_margin_with_existing_fuser"], 6.0)
        self.assertGreater(heavy["required_thermal_resistance_c_per_w_for_existing_heater"], 0.30)


class LedThermalFeedForwardTests(unittest.TestCase):
    def test_payload_heats_black_groups_more_than_blank_groups(self) -> None:
        case = simulate_led_thermal_case("left_half_black")
        self.assertGreater(case["max_temp_rise_c"], case["min_temp_rise_c"] + 2.0)
        self.assertLess(case["worst_raw_relative_output"], 0.995)

    def test_feedforward_is_bounded_and_reduces_latent_error(self) -> None:
        summary = led_thermal_summary()
        self.assertTrue(summary["compensation_bounded"])
        self.assertGreater(abs(summary["worst_uncompensated_latent_error_v"]), 0.5)
        self.assertLess(abs(summary["worst_compensated_latent_error_v"]), 0.1)



class Ofp1RealtimeSpoolTests(unittest.TestCase):
    def test_rev_e_ring_only_covers_about_22ms_not_100ms(self) -> None:
        summary = realtime_spool_summary()
        self.assertGreater(summary["revE_pause_tolerance_ms"], 20.0)
        self.assertLess(summary["revE_pause_tolerance_ms"], 25.0)
        self.assertGreater(summary["required_buffer_bytes_for_100ms_pause"], summary["revE_32_line_ring_buffer_bytes"] * 4)
        case = next(c for c in summary["cases"] if c["case"] == "revE_32_line_ring_10ms_target_only")
        self.assertFalse(case["can_finish_streaming_without_underrun"])

    def test_full_speed_at_75pct_cannot_sustain_12ppm_worst_case(self) -> None:
        summary = realtime_spool_summary()
        case = next(c for c in summary["cases"] if c["case"] == "usb_fs_75pct_worst_case_12ppm_no_margin")
        self.assertLess(case["host_surplus_bytes_per_s"], 0.0)
        self.assertFalse(case["can_finish_streaming_without_underrun"])
        self.assertFalse(summary["full_page_payload_fits_in_rp2040_sram"])

    def test_high_speed_or_slow_mode_with_larger_ring_passes_buffer_gate(self) -> None:
        cases = {c["case"]: c for c in realtime_spool_summary()["cases"]}
        self.assertTrue(cases["usb_hs_12ppm_128KiB_ring_passes_100ms"]["can_finish_streaming_without_underrun"])
        self.assertTrue(cases["usb_fs_degraded_8ppm_128KiB_ring_passes_100ms"]["can_finish_streaming_without_underrun"])
        self.assertGreater(max_ppm_for_host_utilization(max_utilization=0.60), 8.0)


class MotionRegistrationTests(unittest.TestCase):
    def test_open_loop_half_percent_error_is_tens_of_lines(self) -> None:
        err = open_loop_scale_error(speed_error_fraction=0.005)
        self.assertEqual(err["verdict"], "fail")
        self.assertAlmostEqual(err["page_scale_error_lines"], 33.0, delta=0.1)

    def test_encoder_resolution_gate_rejects_2048_accepts_4096(self) -> None:
        low = encoder_resolution(EncoderSpec("2048", 2048))
        high = encoder_resolution(EncoderSpec("4096", 4096))
        interp = encoder_resolution(EncoderSpec("2048_interp", 2048, interpolation=4))
        self.assertFalse(low["passes_quarter_line_quantization_gate"])
        self.assertTrue(high["passes_quarter_line_quantization_gate"])
        self.assertTrue(interp["passes_quarter_line_quantization_gate"])

    def test_registration_timestamp_jitter_gate(self) -> None:
        self.assertTrue(sensor_timestamp_error(timestamp_jitter_us=150.0)["passes_quarter_line_gate"])
        self.assertFalse(sensor_timestamp_error(timestamp_jitter_us=300.0)["passes_quarter_line_gate"])
        summary = motion_registration_summary()
        self.assertTrue(summary["recommended_encoder"]["passes_quarter_line_quantization_gate"])


class OpticalMtfTests(unittest.TestCase):
    def test_spot_fwhm_gate_has_sharp_pass_fail_boundary(self) -> None:
        self.assertTrue(optical_case(45.0)["passes_revG_optical_gate"])
        self.assertFalse(optical_case(50.0)["passes_revG_optical_gate"])
        summary = optical_mtf_summary()
        self.assertGreater(summary["max_gaussian_spot_fwhm_um_for_mtf_gate"], 45.0)
        self.assertLess(summary["max_gaussian_spot_fwhm_um_for_mtf_gate"], 47.0)

    def test_bad_wide_spot_fails_both_mtf_and_crosstalk(self) -> None:
        bad = optical_case(85.0)
        self.assertLess(bad["mtf_at_600dpi_nyquist"], 0.05)
        self.assertGreater(bad["neighbor_pixel_crosstalk_fraction"], 0.45)
        self.assertFalse(bad["passes_revG_optical_gate"])


class FuserThermalSafetyTests(unittest.TestCase):
    def test_firmware_only_fuser_control_has_single_fault_runaway_paths(self) -> None:
        summary = fuser_safety_summary()
        fw = summary["topology_firmware_only"]
        self.assertFalse(fw["verdict_single_fault_safe"])
        self.assertEqual(fw["single_fault_violation_count"], 3)
        fault_names = {tuple(v["faults"])[0] for v in fw["single_fault_violations"]}
        self.assertIn("thermistor_stuck_cold", fault_names)
        self.assertIn("ssr_welded_on", fault_names)

    def test_independent_thermostat_and_fuse_survive_single_faults(self) -> None:
        summary = fuser_safety_summary()
        revg = summary["topology_revG_thermostat_plus_one_shot_fuse"]
        self.assertTrue(revg["verdict_single_fault_safe"])
        self.assertEqual(revg["single_fault_violation_count"], 0)
        topo = FuserSafetyTopology("revG", True, True)
        self.assertFalse(eval_fuser_topology(topo, ["thermistor_stuck_cold"])["heater_continues_above_fault_temp"])
        self.assertFalse(eval_fuser_topology(topo, ["ssr_welded_on"])["heater_continues_above_fault_temp"])



class EraseGhostBudgetTests(unittest.TestCase):
    def test_missing_erase_station_fails_and_revG_dose_passes(self) -> None:
        summary = erase_summary()
        self.assertEqual(summary["pre_revG_as_documented"]["verdict"], "fail_ghost_memory_gate")
        self.assertTrue(summary["revG_requirement"]["passes_energy_window"])
        self.assertGreater(summary["revG_requirement"]["dose_margin_ratio"], 1.2)
        self.assertLess(summary["revG_requirement"]["over_image_exposure_ratio"], 5.0)

    def test_ghost_distance_is_one_drum_circumference(self) -> None:
        summary = erase_summary()
        self.assertAlmostEqual(summary["ghost_test_pattern"]["predicted_repeat_distance_mm"], 94.2478, delta=0.01)
        self.assertAlmostEqual(drum_rotation_period_s(), summary["ghost_test_pattern"]["drum_rotation_period_s"], delta=1e-9)
        self.assertGreater(required_erase_energy_uj_cm2(), 0.55)


class HVDischargeBleedTests(unittest.TestCase):
    def test_no_bleeder_is_an_explicit_counterexample(self) -> None:
        counter = no_bleed_counterexample()
        self.assertEqual(counter["verdict"], "fail_no_guaranteed_touch_safe_decay")
        self.assertGreater(counter["voltage_after_2s_without_specified_bleed_v"], 1000.0)

    def test_default_bleeders_pass_normal_and_single_fault_gates(self) -> None:
        summary = hv_discharge_summary()
        self.assertTrue(summary["all_nodes_pass_normal_60v"])
        self.assertTrue(summary["all_nodes_pass_single_fault_120v"])
        transfer = next(n for n in summary["nodes"] if n["name"] == "TRANSFER_ROLLER_OUTPUT")
        self.assertLess(transfer["voltage_after_2s_single_fault_v"], 120.0)

    def test_too_large_single_bleeder_fails_high_capacitance_node(self) -> None:
        bad = evaluate_node(HVNode("BAD_BIG_CAP", 2500.0, 10.0, 100.0))
        self.assertFalse(bad["passes_single_fault_120v_gate"])


class EnvironmentDeratingTests(unittest.TestCase):
    def test_humidity_sensitive_toner_loses_charge_at_80rh(self) -> None:
        self.assertAlmostEqual(toner_q_over_m_uc_g(20.0), -80.0)
        self.assertAlmostEqual(toner_q_over_m_uc_g(80.0), -57.0)
        humid = evaluate_environment(EnvironmentCase("humid", 80.0, "plain", 8.0))
        self.assertLess(humid["charge_factor_vs_50rh"], 0.86)
        self.assertNotEqual(humid["verdict"], "run_nominal_with_logged_environment")

    def test_environment_summary_forces_humid_plain_calibration(self) -> None:
        summary = environment_summary()
        self.assertTrue(summary["humid_plain_requires_calibration"])
        film = next(c for c in summary["cases"] if c["name"] == "humid_80rh_film_or_label")
        self.assertGreaterEqual(film["open_loop_transfer_center_v_before_impedance_sniff"], 1800.0)


class EmissionsContainmentTests(unittest.TestCase):
    def test_fan_filter_only_does_not_solve_high_emitter(self) -> None:
        summary = emissions_summary()
        self.assertTrue(summary["fan_filter_only_is_not_enough_for_high_emitter"])
        self.assertTrue(summary["output_tray_capture_changes_verdict"])

    def test_capture_efficiency_changes_modeled_concentration(self) -> None:
        naked = evaluate_emission_case(EmissionCase("naked", 1.0e12))
        captured = evaluate_emission_case(EmissionCase("captured", 1.0e12, source_capture_efficiency=0.90, output_tray_capture_efficiency=0.09))
        self.assertGreater(naked["modeled_steady_state_particles_per_m3"], captured["modeled_steady_state_particles_per_m3"] * 50.0)
        self.assertTrue(captured["passes_internal_review_threshold"])


class RegistrationEdgeBudgetTests(unittest.TestCase):
    def test_5120_bar_has_less_than_one_mm_edge_slack(self) -> None:
        summary = registration_summary()
        self.assertFalse(summary["current_5120_bar"]["passes_1mm_each_side_slack_goal"])
        self.assertLess(summary["current_5120_bar"]["lateral_slack_each_side_mm"], 0.40)
        self.assertGreater(summary["old_test_plan_plus_minus_1mm"]["error_lines"], 23.0)

    def test_5184_pixel_bar_is_byte_aligned_slack_fix(self) -> None:
        target = EngineTargets()
        min_px = minimum_pixels_for_lateral_slack(target, 1.0)
        self.assertGreater(min_px, 5120)
        self.assertEqual(round_up_to_byte_aligned_pixels(min_px), 5184)
        proposed = registration_summary()["recommended_revG_LED_or_margins"]
        self.assertGreater(proposed["proposed_lateral_slack_each_side_mm"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
