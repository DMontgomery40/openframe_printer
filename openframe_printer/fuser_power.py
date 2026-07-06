from __future__ import annotations

"""Continuous fuser paper-load budget.

The original fuser model simulates roller warm-up and free-air losses. It does
not charge the fuser for the thing a printer actually does: heat moving paper,
moisture, and toner at 12 pages/minute. Rev F adds that load path and compares
it with the heater's steady-state margin after roller/environment losses.

This is a first-order energy balance, not a fusing-quality proof. It is meant
to catch impossible heater/insulation/media combinations before hardware.
"""

from dataclasses import asdict, dataclass

from .engine_math import EngineTargets, dense_black_toner_per_page_g
from .fuser_model import FuserModel


@dataclass(frozen=True)
class FuserMediaCase:
    name: str
    basis_weight_g_m2: float
    moisture_fraction: float
    evaporated_moisture_fraction: float
    paper_exit_bulk_temp_c: float
    coverage: float = 0.05


@dataclass(frozen=True)
class FuserThermalAssumptions:
    ambient_c: float = 25.0
    paper_specific_heat_j_g_c: float = 1.34
    water_specific_heat_j_g_c: float = 4.18
    water_latent_heat_j_g: float = 2257.0
    toner_specific_heat_j_g_c: float = 1.50
    toner_softening_energy_j_g: float = 35.0
    required_steady_margin_fraction: float = 0.10


DEFAULT_CASES: tuple[FuserMediaCase, ...] = (
    FuserMediaCase("75gsm_plain_nominal", 75.0, 0.05, 0.10, 120.0),
    FuserMediaCase("90gsm_damp_heavy", 90.0, 0.08, 0.25, 125.0),
    FuserMediaCase("60gsm_dry_light", 60.0, 0.02, 0.03, 115.0),
)


def _page_area_m2(target: EngineTargets) -> float:
    return (target.page_width_mm / 1000.0) * (target.letter_length_mm / 1000.0)


def paper_load_case(
    media: FuserMediaCase,
    target: EngineTargets | None = None,
    fuser: FuserModel | None = None,
    assume: FuserThermalAssumptions | None = None,
) -> dict:
    t = target or EngineTargets()
    f = fuser or FuserModel()
    a = assume or FuserThermalAssumptions(ambient_c=f.ambient_c)
    page_area_m2 = _page_area_m2(t)
    pages_per_s = t.ppm / 60.0
    paper_g_per_page = media.basis_weight_g_m2 * page_area_m2
    paper_g_s = paper_g_per_page * pages_per_s
    dry_fiber_g_s = paper_g_s * (1.0 - media.moisture_fraction)
    water_g_s = paper_g_s * media.moisture_fraction
    delta_paper_c = max(0.0, media.paper_exit_bulk_temp_c - a.ambient_c)
    water_sensible_delta_c = max(0.0, min(media.paper_exit_bulk_temp_c, 100.0) - a.ambient_c)

    dry_paper_w = dry_fiber_g_s * a.paper_specific_heat_j_g_c * delta_paper_c
    water_sensible_w = water_g_s * a.water_specific_heat_j_g_c * water_sensible_delta_c
    water_evap_w = water_g_s * media.evaporated_moisture_fraction * a.water_latent_heat_j_g
    toner_g_s = dense_black_toner_per_page_g(t, media.coverage) * pages_per_s
    toner_w = toner_g_s * (a.toner_specific_heat_j_g_c * delta_paper_c + a.toner_softening_energy_j_g)
    total_load_w = dry_paper_w + water_sensible_w + water_evap_w + toner_w

    idle_loss_w = max(0.0, (f.target_c - f.ambient_c) / f.thermal_resistance_c_per_w)
    available_for_media_w = max(0.0, f.heater_power_w - idle_loss_w)
    remaining_margin_w = available_for_media_w - total_load_w
    required_margin_w = f.heater_power_w * a.required_steady_margin_fraction
    pass_margin = remaining_margin_w >= required_margin_w
    required_heater_w_for_margin = idle_loss_w + total_load_w + required_margin_w
    required_thermal_resistance_for_existing_heater = (
        (f.target_c - f.ambient_c) / max(1e-9, f.heater_power_w - total_load_w - required_margin_w)
        if f.heater_power_w > total_load_w + required_margin_w else float("inf")
    )
    slow_ppm_for_margin = (
        t.ppm * max(0.0, (available_for_media_w - required_margin_w)) / total_load_w
        if total_load_w > 0.0 else t.ppm
    )

    return {
        "case": media.name,
        "media": asdict(media),
        "page_area_m2": page_area_m2,
        "pages_per_second": pages_per_s,
        "paper_g_per_page": paper_g_per_page,
        "paper_mass_flow_g_s": paper_g_s,
        "toner_mass_flow_g_s": toner_g_s,
        "load_w": {
            "dry_paper_sensible": dry_paper_w,
            "water_sensible": water_sensible_w,
            "water_evaporation": water_evap_w,
            "toner_sensible_and_softening": toner_w,
            "total_media_load": total_load_w,
        },
        "heater_power_w": f.heater_power_w,
        "idle_loss_w_from_existing_Rth": idle_loss_w,
        "available_for_media_w_after_idle_loss": available_for_media_w,
        "remaining_margin_w": remaining_margin_w,
        "required_margin_w": required_margin_w,
        "passes_steady_margin_gate": pass_margin,
        "required_heater_w_for_margin": required_heater_w_for_margin,
        "required_thermal_resistance_c_per_w_for_existing_heater": required_thermal_resistance_for_existing_heater,
        "slow_to_ppm_for_margin_with_existing_fuser": slow_ppm_for_margin,
        "verdict": "run" if pass_margin else "insulate_raise_power_or_slow_media",
    }


def fuser_power_summary(
    target: EngineTargets | None = None,
    fuser: FuserModel | None = None,
    assume: FuserThermalAssumptions | None = None,
) -> dict:
    t = target or EngineTargets()
    f = fuser or FuserModel()
    a = assume or FuserThermalAssumptions(ambient_c=f.ambient_c)
    cases = [paper_load_case(c, t, f, a) for c in DEFAULT_CASES]
    return {
        "revision": "M1-REV-F",
        "finding": (
            "The warm-up fuser model was not a print-throughput model. With the existing "
            "800 W heater and 0.235 C/W loss assumption, nominal 75 gsm media has only a "
            "thin continuous margin and damp/heavy media fails the first-build gate."
        ),
        "assumptions": asdict(a),
        "fuser_model": asdict(f),
        "engine_ppm": t.ppm,
        "cases": cases,
        "all_cases_pass_steady_margin_gate": all(c["passes_steady_margin_gate"] for c in cases),
        "first_build_requirement": (
            "Either improve insulation to the generated Rth target, raise heater power, or "
            "firmware-limit heavy/damp media speed. Do not claim 12 ppm on all plain-paper "
            "cases from the warm-up curve alone."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(fuser_power_summary(), indent=2))
