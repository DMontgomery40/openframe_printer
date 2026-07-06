from __future__ import annotations

"""Rev C PIDC-first calibration engine (hypothesis H1, implemented).

Rev B proposed storing a target latent-voltage window instead of a blind
LED-energy constant, with a coupon rig and a lookup fit. This module is that
proposal as running code:

* a parametric photo-induced discharge curve (PIDC) model,
* a dependency-free least-squares fitter for rig measurements,
* the inverse problem the firmware actually needs: choose an LED pulse width
  that lands the drum surface inside the target latent-voltage window,
* a synthetic-rig demonstration with probe noise and an automated version of
  the H1 kill criteria, so the hypothesis carries a pass/fail number instead
  of an intention.

Model form: the classic saturating exponential discharge

    V(E) = V_r + (V_0 - V_r) * exp(-E / E_a)

with V_0 the charged surface potential, V_r the residual potential, and E_a
the characteristic exposure (uJ/cm^2). This is an engineering approximation,
not a claim about carrier transport; its job is to interpolate rig
measurements stably. Latent-image hold between exposure and development is a
single contrast-retention time constant tau_latent_s, to be measured on the
H1 rig at the geometric delay derived in station_map.py.

Sign convention: potentials are negative (negative-charging OPC); energies
are uJ/cm^2 everywhere. The Fuji Electric negative-charge OPC window (0.15 to
0.80 uJ/cm^2 to discharge -600 V to -100 V) anchors the default parameter
ranges.
"""

from dataclasses import dataclass, asdict
import math
import random

from .units import mw_cm2_to_uj_cm2_per_us


@dataclass(frozen=True)
class PidcModel:
    v_charge_v: float      # V_0, e.g. -600.0
    v_residual_v: float    # V_r, e.g. -60.0
    e_char_uj_cm2: float   # E_a
    tau_latent_s: float = 2.0

    def surface_potential_v(self, exposure_uj_cm2: float) -> float:
        return self.v_residual_v + (self.v_charge_v - self.v_residual_v) * math.exp(
            -exposure_uj_cm2 / self.e_char_uj_cm2
        )

    def exposure_for_potential_uj_cm2(self, target_v: float) -> float:
        """Invert V(E). target_v must lie strictly between V_r and V_0."""
        span = self.v_charge_v - self.v_residual_v
        remaining = target_v - self.v_residual_v
        if span == 0.0 or remaining / span <= 0.0:
            raise ValueError(
                f"target {target_v} V is not reachable between residual "
                f"{self.v_residual_v} V and charge {self.v_charge_v} V"
            )
        return -self.e_char_uj_cm2 * math.log(remaining / span)

    def contrast_retention(self, delay_ms: float) -> float:
        return math.exp(-(delay_ms / 1000.0) / self.tau_latent_s)


def model_from_discharge_requirement(
    energy_to_discharge_uj_cm2: float,
    v_charge_v: float = -600.0,
    v_discharged_v: float = -100.0,
    v_residual_v: float = -60.0,
) -> PidcModel:
    """Build a model from the datasheet-style spec 'E uJ/cm^2 takes V_0 to V_d'."""
    span = v_charge_v - v_residual_v
    remaining = v_discharged_v - v_residual_v
    e_char = energy_to_discharge_uj_cm2 / math.log(span / remaining)
    return PidcModel(v_charge_v=v_charge_v, v_residual_v=v_residual_v, e_char_uj_cm2=e_char)


def fit_pidc(
    measurements: list[tuple[float, float]],
    v_charge_v: float,
    residual_grid_v: tuple[float, float] = (-150.0, -5.0),
    e_char_grid_uj_cm2: tuple[float, float] = (0.03, 0.60),
) -> PidcModel:
    """Least-squares fit of (exposure_uJ_cm2, measured_V) rig points.

    Grid search over (V_r, E_a) followed by local refinement. Dependency-free
    and monotonic-model-stable; a coupon rig produces tens of points, so the
    cost is irrelevant.
    """

    def sse(v_r: float, e_a: float) -> float:
        model = PidcModel(v_charge_v=v_charge_v, v_residual_v=v_r, e_char_uj_cm2=e_a)
        return sum((model.surface_potential_v(e) - v) ** 2 for e, v in measurements)

    best = (float("inf"), residual_grid_v[0], e_char_grid_uj_cm2[0])
    steps = 60
    for i in range(steps + 1):
        v_r = residual_grid_v[0] + (residual_grid_v[1] - residual_grid_v[0]) * i / steps
        for j in range(steps + 1):
            e_a = (
                e_char_grid_uj_cm2[0]
                + (e_char_grid_uj_cm2[1] - e_char_grid_uj_cm2[0]) * j / steps
            )
            err = sse(v_r, e_a)
            if err < best[0]:
                best = (err, v_r, e_a)

    _, v_r, e_a = best
    v_step = (residual_grid_v[1] - residual_grid_v[0]) / steps
    e_step = (e_char_grid_uj_cm2[1] - e_char_grid_uj_cm2[0]) / steps
    for _ in range(40):
        improved = False
        for dv, de in ((v_step, 0), (-v_step, 0), (0, e_step), (0, -e_step)):
            candidate_v = v_r + dv
            candidate_e = e_a + de
            if candidate_e <= 0.0:
                continue
            if sse(candidate_v, candidate_e) < sse(v_r, e_a):
                v_r, e_a = candidate_v, candidate_e
                improved = True
        if not improved:
            v_step /= 2.0
            e_step /= 2.0
            if v_step < 0.01 and e_step < 0.0001:
                break
    return PidcModel(v_charge_v=v_charge_v, v_residual_v=v_r, e_char_uj_cm2=e_a)


@dataclass(frozen=True)
class PulseChoice:
    target_latent_v: float
    exposure_needed_uj_cm2: float
    pulse_width_us: float
    fraction_of_line_period: float
    within_line_budget: bool


def choose_pulse_width(
    model: PidcModel,
    target_latent_v: float,
    led_irradiance_mw_cm2: float,
    line_period_us: float,
    max_duty_fraction: float = 0.6,
) -> PulseChoice:
    """The firmware-facing inversion: latent-voltage target -> LED pulse width.

    Exposure integrates irradiance over the pulse: E = irradiance * t. The
    duty ceiling leaves room for shift/latch and thermal recovery inside the
    line period.
    """
    exposure = model.exposure_for_potential_uj_cm2(target_latent_v)
    rate = mw_cm2_to_uj_cm2_per_us(led_irradiance_mw_cm2)
    pulse_us = exposure / rate
    fraction = pulse_us / line_period_us
    return PulseChoice(
        target_latent_v=target_latent_v,
        exposure_needed_uj_cm2=round(exposure, 4),
        pulse_width_us=round(pulse_us, 2),
        fraction_of_line_period=round(fraction, 4),
        within_line_budget=fraction <= max_duty_fraction,
    )


def synthetic_rig_demo(
    seed: int = 20260706,
    probe_noise_v: float = 8.0,
    energies_uj_cm2: tuple[float, ...] = (0.10, 0.15, 0.25, 0.35, 0.45, 0.60, 0.80, 1.00),
    repeats: int = 3,
    led_irradiance_mw_cm2: float = 15.0,
    line_period_us: float = 682.8,
    geometric_delay_ms: float = 160.0,
) -> dict:
    """Simulate one H1 coupon-rig session end to end and score the kill criteria.

    A hidden 'true' OPC (parameters the fit never sees) generates noisy probe
    readings; the fitter recovers a model; the pulse chooser uses the fitted
    model; the score compares against the hidden truth. This is the software
    proof that the calibration loop closes -- the physical rig then only has
    to beat the same noise number.
    """
    rng = random.Random(seed)
    truth = PidcModel(
        v_charge_v=-600.0, v_residual_v=-65.0, e_char_uj_cm2=0.19, tau_latent_s=2.4
    )

    measurements: list[tuple[float, float]] = []
    for energy in energies_uj_cm2:
        for _ in range(repeats):
            reading = truth.surface_potential_v(energy) + rng.gauss(0.0, probe_noise_v)
            measurements.append((energy, round(reading, 2)))

    fitted = fit_pidc(measurements, v_charge_v=-600.0)

    check_points = [0.05 * k for k in range(2, 21)]  # 0.10 .. 1.00 uJ/cm^2
    max_prediction_error_v = max(
        abs(fitted.surface_potential_v(e) - truth.surface_potential_v(e))
        for e in check_points
    )

    target_latent_v = -100.0
    pulse = choose_pulse_width(fitted, target_latent_v, led_irradiance_mw_cm2, line_period_us)
    achieved_v = truth.surface_potential_v(
        pulse.pulse_width_us * mw_cm2_to_uj_cm2_per_us(led_irradiance_mw_cm2)
    )
    landing_error_v = abs(achieved_v - target_latent_v)

    retention = truth.contrast_retention(geometric_delay_ms)

    kill_criteria = {
        "max_prediction_error_v": round(max_prediction_error_v, 2),
        "prediction_error_limit_v": 25.0,
        "prediction_ok": max_prediction_error_v <= 25.0,
        "pulse_landing_error_v": round(landing_error_v, 2),
        "pulse_landing_limit_v": 30.0,
        "pulse_landing_ok": landing_error_v <= 30.0,
        "contrast_retention_at_geometric_delay": round(retention, 4),
        "contrast_retention_limit": 0.9,
        "retention_ok": retention >= 0.9,
    }
    kill_criteria["h1_loop_closes"] = all(
        (kill_criteria["prediction_ok"], kill_criteria["pulse_landing_ok"], kill_criteria["retention_ok"])
    )

    return {
        "hidden_truth": asdict(truth),
        "rig_session": {
            "probe_noise_v_sigma": probe_noise_v,
            "energies_uj_cm2": list(energies_uj_cm2),
            "repeats_per_energy": repeats,
            "n_measurements": len(measurements),
            "measurements": measurements,
        },
        "fitted_model": asdict(fitted),
        "pulse_choice": asdict(pulse),
        "achieved_latent_v_under_truth": round(achieved_v, 2),
        "geometric_delay_ms": geometric_delay_ms,
        "kill_criteria": kill_criteria,
        "notes": [
            "The hidden truth model is never visible to the fitter; only noisy probe readings are.",
            "A physical rig replaces synthetic readings with probe measurements; the same scoring applies.",
            "Landing the latent voltage, not emitting a fixed optical energy, is the calibration contract.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(synthetic_rig_demo(), indent=2))
