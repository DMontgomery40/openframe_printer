from __future__ import annotations

"""Rev D feasibility budget for hypothesis H8: developer roller as probe.

The Rev C hypothesis was good but unbudgeted: using DEV_MON as an in-situ PIDC
sensor only works if the latent-voltage pattern induces a signal above the
monitor noise floor. This module computes the first-order capacitance/current
budget so the idea can be accepted, resized, or killed before hardware is built.

This is deliberately a simple physics budget: C = eps0 * eps_r * A / gap,
Q = C * deltaV, I = Q / transit_time. The physical H1/H8 rig replaces the
parallel-plate estimate with measured coupling; the required monitor noise
floor and patch-size scaling stay useful either way.
"""

from dataclasses import dataclass, asdict

from .engine_math import EngineTargets, line_pitch_mm, process_speed_mm_s

EPS0_F_PER_M = 8.8541878128e-12


@dataclass(frozen=True)
class DeveloperProbeBudget:
    group_px: int
    group_lines: int
    dpi: int
    patch_width_mm: float
    patch_process_mm: float
    developer_gap_um: float
    effective_eps_r: float
    process_speed_mm_s: float
    latent_voltage_span_v: float
    capacitance_pf: float
    full_scale_signal_charge_nc: float
    patch_transit_ms: float
    full_scale_ideal_current_na: float
    eight_step_current_spacing_na: float
    required_monitor_noise_na_rms_for_3sigma_steps: float
    minimum_useful_monitor_bandwidth_hz: float
    h8_plain_monitor_assumption_ok: bool
    note: str


def developer_probe_budget(
    target: EngineTargets | None = None,
    group_px: int = 64,
    group_lines: int | None = None,
    developer_gap_um: float = 150.0,
    effective_eps_r: float = 1.3,
    latent_voltage_span_v: float = 500.0,
) -> DeveloperProbeBudget:
    """Estimate the DEV_MON signal for one square calibration patch.

    The default patch is 64 pixels wide by 64 lines tall at 600 dpi, matching
    the Rev C idea of 64-pixel calibration groups. A staircase with 8 exposure
    levels needs adjacent steps resolvable, so the useful noise requirement is
    based on full-scale current / 7 / 3.
    """
    t = target or EngineTargets()
    lines = group_px if group_lines is None else group_lines
    pitch_mm = line_pitch_mm(t.dpi)
    width_mm = group_px * pitch_mm
    process_mm = lines * pitch_mm
    area_m2 = (width_mm / 1000.0) * (process_mm / 1000.0)
    gap_m = developer_gap_um * 1e-6
    capacitance_f = EPS0_F_PER_M * effective_eps_r * area_m2 / gap_m
    charge_c = capacitance_f * latent_voltage_span_v
    speed = process_speed_mm_s(t)
    transit_s = process_mm / speed
    current_a = charge_c / transit_s
    step_current_a = current_a / 7.0
    required_noise_a = step_current_a / 3.0
    bandwidth_hz = speed / process_mm
    plain_ok = required_noise_a >= 1.0e-9  # a plain scaled HV monitor is unlikely to be quieter than this.
    note = (
        "Budget says H8 should not rely on a generic voltage readback. "
        "Use a quiet DEV_MON current-sense/TIA mode or widen the calibration patch."
        if not plain_ok
        else "Budget is large enough for a deliberately quiet DEV_MON current-sense mode; still verify on H1/H8 rig."
    )
    return DeveloperProbeBudget(
        group_px=group_px,
        group_lines=lines,
        dpi=t.dpi,
        patch_width_mm=round(width_mm, 4),
        patch_process_mm=round(process_mm, 4),
        developer_gap_um=developer_gap_um,
        effective_eps_r=effective_eps_r,
        process_speed_mm_s=round(speed, 3),
        latent_voltage_span_v=latent_voltage_span_v,
        capacitance_pf=round(capacitance_f * 1e12, 3),
        full_scale_signal_charge_nc=round(charge_c * 1e9, 4),
        patch_transit_ms=round(transit_s * 1000.0, 3),
        full_scale_ideal_current_na=round(current_a * 1e9, 3),
        eight_step_current_spacing_na=round(step_current_a * 1e9, 3),
        required_monitor_noise_na_rms_for_3sigma_steps=round(required_noise_a * 1e9, 3),
        minimum_useful_monitor_bandwidth_hz=round(bandwidth_hz, 2),
        h8_plain_monitor_assumption_ok=plain_ok,
        note=note,
    )


def recommended_patch_for_monitor_noise(
    monitor_noise_na_rms: float = 0.5,
    snr_sigma: float = 3.0,
    candidate_sizes_px: tuple[int, ...] = (32, 64, 96, 128, 192, 256),
) -> dict:
    candidates = [developer_probe_budget(group_px=size) for size in candidate_sizes_px]
    required_spacing = monitor_noise_na_rms * snr_sigma
    passing = [c for c in candidates if c.eight_step_current_spacing_na >= required_spacing]
    chosen = passing[0] if passing else candidates[-1]
    return {
        "monitor_noise_na_rms": monitor_noise_na_rms,
        "required_adjacent_step_spacing_na": round(required_spacing, 3),
        "chosen_patch": asdict(chosen),
        "all_candidates": [asdict(c) for c in candidates],
        "verdict": (
            "H8 is feasible in this first-order budget if DEV_MON has a real current-sense mode; "
            "a 128x128 patch is the first default that clears 0.5 nA RMS with 3-sigma step spacing."
            if passing
            else "No candidate clears the requested monitor noise; H8 needs a better analog front-end or larger patch."
        ),
    }


def dev_probe_summary() -> dict:
    return {
        "revision": "M1-REV-D",
        "hypothesis": "H8 developer roller as in-situ electrostatic probe",
        "budget_model": "C = eps0 * eps_r * A/gap; Q = C * deltaV; I = Q / patch_transit_time",
        "nominal_64x64_patch": asdict(developer_probe_budget(group_px=64)),
        "recommendation_for_0_5nA_monitor": recommended_patch_for_monitor_noise(0.5),
        "engineering_consequence": (
            "H8 survives as plausible but only with an explicit DEV_MON current-sense/TIA mode. "
            "The old wording 'watch DEV_MON' was too vague; the analog requirement is now numeric."
        ),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(dev_probe_summary(), indent=2))
