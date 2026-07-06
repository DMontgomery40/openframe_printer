from __future__ import annotations

"""Payload-derived LED printhead thermal droop feed-forward (H9).

Rev C proposed H9 as a hypothesis: compute LED thermal droop from the raster
payload already being shifted to the printhead. Rev F turns that into a small
engine. It is not a substitute for the photodiode bar calibration rig; it is a
feed-forward prior that says which LED groups are likely to be dimmer before the
sensor closes the loop.
"""

from dataclasses import asdict, dataclass
import math

from .engine_math import EngineTargets, line_period_us, lines_down
from .pidc_model import model_from_discharge_requirement


@dataclass(frozen=True)
class LedThermalConfig:
    group_px: int = 64
    nominal_pulse_us: float = 30.0
    full_line_duty_junction_rise_c: float = 80.0
    thermal_tau_s: float = 2.0
    light_output_temp_coeff_per_c: float = -0.0030
    max_pulse_compensation: float = 1.08
    ambient_c: float = 25.0


def _coverage_profile(case: str, groups: int) -> list[float]:
    if case == "solid_black_page":
        return [1.0] * groups
    if case == "left_half_black":
        return [1.0 if i < groups // 2 else 0.0 for i in range(groups)]
    if case == "center_bar":
        return [1.0 if groups * 0.4 <= i < groups * 0.6 else 0.02 for i in range(groups)]
    if case == "office_5pct_uniform":
        return [0.05] * groups
    raise ValueError(f"unknown LED thermal case {case!r}")


def simulate_led_thermal_case(
    case: str = "left_half_black",
    target: EngineTargets | None = None,
    cfg: LedThermalConfig | None = None,
) -> dict:
    t = target or EngineTargets()
    c = cfg or LedThermalConfig()
    if t.led_pixels % c.group_px:
        raise ValueError("LED pixels must be divisible by group size")
    groups = t.led_pixels // c.group_px
    line_period_s = line_period_us(t) / 1_000_000.0
    page_lines = lines_down(t.letter_length_mm, t.dpi)
    coverage = _coverage_profile(case, groups)
    temp_rise = [0.0] * groups
    alpha = 1.0 - math.exp(-line_period_s / c.thermal_tau_s)
    duty_scale = c.nominal_pulse_us / line_period_us(t)
    for _line in range(page_lines):
        for i, cov in enumerate(coverage):
            steady_rise = c.full_line_duty_junction_rise_c * cov * duty_scale
            temp_rise[i] += (steady_rise - temp_rise[i]) * alpha

    raw_relative_output = [max(0.0, 1.0 + c.light_output_temp_coeff_per_c * rise) for rise in temp_rise]
    compensation = [min(c.max_pulse_compensation, 1.0 / out if out > 0 else c.max_pulse_compensation) for out in raw_relative_output]
    compensated_relative_output = [out * comp for out, comp in zip(raw_relative_output, compensation)]

    pidc = model_from_discharge_requirement(0.45)
    worst_raw_output = min(raw_relative_output)
    worst_comp_output = min(compensated_relative_output)
    uncompensated_v = pidc.surface_potential_v(0.45 * worst_raw_output)
    compensated_v = pidc.surface_potential_v(0.45 * worst_comp_output)

    hottest = max(range(groups), key=lambda i: temp_rise[i])
    coolest = min(range(groups), key=lambda i: temp_rise[i])
    return {
        "case": case,
        "config": asdict(c),
        "groups": groups,
        "page_lines": page_lines,
        "line_period_us": line_period_us(t),
        "payload_coverage_by_group": coverage,
        "end_of_page_temp_rise_c_by_group": temp_rise,
        "end_of_page_relative_output_by_group_before_comp": raw_relative_output,
        "pulse_compensation_multiplier_by_group": compensation,
        "relative_output_by_group_after_comp": compensated_relative_output,
        "hottest_group": hottest,
        "coolest_group": coolest,
        "max_temp_rise_c": max(temp_rise),
        "min_temp_rise_c": min(temp_rise),
        "worst_raw_relative_output": worst_raw_output,
        "worst_compensated_relative_output": worst_comp_output,
        "uncompensated_worst_latent_v_at_0_45uJ_target": uncompensated_v,
        "compensated_worst_latent_v_at_0_45uJ_target": compensated_v,
        "uncompensated_latent_error_v_vs_minus100": uncompensated_v - (-100.0),
        "compensated_latent_error_v_vs_minus100": compensated_v - (-100.0),
    }


def led_thermal_summary(target: EngineTargets | None = None, cfg: LedThermalConfig | None = None) -> dict:
    t = target or EngineTargets()
    c = cfg or LedThermalConfig()
    cases = [simulate_led_thermal_case(case, t, c) for case in (
        "office_5pct_uniform", "left_half_black", "center_bar", "solid_black_page"
    )]
    worst = max(cases, key=lambda row: abs(row["uncompensated_latent_error_v_vs_minus100"]))
    return {
        "revision": "M1-REV-F",
        "hypothesis": "H9 payload-derived LED thermal-droop feed-forward",
        "finding": (
            "The raster payload predicts which printhead groups are thermally stressed. "
            "Use that prediction as a bounded pulse-width feed-forward before the photodiode/PIDC rig trims it."
        ),
        "cases": cases,
        "worst_uncompensated_case": worst["case"],
        "worst_uncompensated_latent_error_v": worst["uncompensated_latent_error_v_vs_minus100"],
        "worst_compensated_latent_error_v": max(
            abs(row["compensated_latent_error_v_vs_minus100"]) for row in cases
        ),
        "compensation_bounded": all(
            max(row["pulse_compensation_multiplier_by_group"]) <= c.max_pulse_compensation + 1e-9
            for row in cases
        ),
        "rig_gate": (
            "Run a solid-band page under the photodiode jig; feed-forward must reduce measured "
            "end-of-page group density droop by at least 50% without exceeding the pulse cap."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(led_thermal_summary(), indent=2))
