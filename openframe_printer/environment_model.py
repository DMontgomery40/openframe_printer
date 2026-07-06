from __future__ import annotations

"""Rev G: humidity/material derating for toner charge and transfer.

The earlier transfer controller measures paper/nip impedance, but the design did
not tie humidity, toner charge, and media class together. This module keeps RH
out of the realm of vague advice by emitting a deterministic derating table and
by forcing 80% RH / unknown toner into calibration instead of pretending the
nominal developer and transfer values are universal.
"""

from dataclasses import dataclass, asdict

from .transfer_model import choose_transfer_current


@dataclass(frozen=True)
class EnvironmentCase:
    name: str
    relative_humidity_percent: float
    media: str
    measured_impedance_mohm: float
    media_transfer_offset_v: float = 0.0


@dataclass(frozen=True)
class TonerChargeModel:
    q_over_m_at_20rh_uc_g: float = -80.0
    q_over_m_at_80rh_uc_g: float = -57.0
    rh_low_percent: float = 20.0
    rh_high_percent: float = 80.0


def toner_q_over_m_uc_g(rh_percent: float, model: TonerChargeModel | None = None) -> float:
    m = model or TonerChargeModel()
    if rh_percent <= m.rh_low_percent:
        return m.q_over_m_at_20rh_uc_g
    if rh_percent >= m.rh_high_percent:
        return m.q_over_m_at_80rh_uc_g
    frac = (rh_percent - m.rh_low_percent) / (m.rh_high_percent - m.rh_low_percent)
    return m.q_over_m_at_20rh_uc_g + frac * (m.q_over_m_at_80rh_uc_g - m.q_over_m_at_20rh_uc_g)


def humidity_transfer_bias_offset_v(rh_percent: float) -> float:
    """Conservative open-loop correction sign only; closed-loop impedance wins.

    Prior art says transfer voltage should decrease as RH rises. This slope is
    deliberately small and only used as a first ramp center before current-mode
    impedance control takes over.
    """
    return -8.0 * (rh_percent - 50.0)


def evaluate_environment(case: EnvironmentCase,
                         model: TonerChargeModel | None = None) -> dict:
    m = model or TonerChargeModel()
    q = toner_q_over_m_uc_g(case.relative_humidity_percent, m)
    q_nominal = toner_q_over_m_uc_g(50.0, m)
    charge_factor = abs(q) / abs(q_nominal)
    transfer = choose_transfer_current(case.measured_impedance_mohm, case=case.name)
    open_loop_center_v = 1600.0 + humidity_transfer_bias_offset_v(case.relative_humidity_percent) + case.media_transfer_offset_v
    if charge_factor < 0.86:
        verdict = "hold_quality_print_run_pidc_dev_bias_and_transfer_sweep"
    elif charge_factor < 0.94:
        verdict = "run_with_density_calibration_required"
    else:
        verdict = "run_nominal_with_logged_environment"
    return {
        **asdict(case),
        "toner_q_over_m_uc_g": q,
        "nominal_50rh_q_over_m_uc_g": q_nominal,
        "charge_factor_vs_50rh": charge_factor,
        "litbsa_charge_loss_percent_20_to_80rh": (abs(m.q_over_m_at_20rh_uc_g) - abs(m.q_over_m_at_80rh_uc_g)) / abs(m.q_over_m_at_20rh_uc_g) * 100.0,
        "open_loop_transfer_center_v_before_impedance_sniff": open_loop_center_v,
        "closed_loop_transfer_choice": transfer.__dict__,
        "verdict": verdict,
    }


def environment_summary() -> dict:
    cases = [
        EnvironmentCase("dry_office_20rh_plain", 20.0, "75gsm_plain", 100.0),
        EnvironmentCase("nominal_office_50rh_plain", 50.0, "75gsm_plain", 30.0),
        EnvironmentCase("humid_80rh_plain", 80.0, "75gsm_plain", 8.0),
        EnvironmentCase("humid_80rh_film_or_label", 80.0, "high_resistivity_film_or_label", 120.0, media_transfer_offset_v=500.0),
    ]
    evaluated = [evaluate_environment(c) for c in cases]
    return {
        "requirement": "humidity is a process variable, not a support note",
        "toner_model_basis": {
            "rh_sensitive_example": "-80 to -57 uC/g from 20% to 80% RH",
            "rh_insensitive_candidate_required": "toner RFQ must report RH sweep; insensitive additives are preferred but not assumed",
        },
        "cases": evaluated,
        "all_cases_have_transfer_decision": all("closed_loop_transfer_choice" in c for c in evaluated),
        "humid_plain_requires_calibration": next(c for c in evaluated if c["name"] == "humid_80rh_plain")["verdict"] != "run_nominal_with_logged_environment",
        "film_offset_v": 500.0,
    }
