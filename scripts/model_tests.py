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


if __name__ == "__main__":
    unittest.main(verbosity=2)
