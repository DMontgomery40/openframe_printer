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

from openframe_printer.engine_math import EngineTargets, process_speed_mm_s  # noqa: E402
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
    interlock_fault_summary,
)
from openframe_printer.halftone import (  # noqa: E402
    bayer_matrix,
    clustered_matrix,
    floyd_steinberg,
    isolated_black_pixels,
    printability_summary,
    screen_halftone,
)
from openframe_printer.toner_budget import TonerAssumptions, toner_mass_balance  # noqa: E402


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

    def test_rev_e_topology_survives_every_single_fault(self) -> None:
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
