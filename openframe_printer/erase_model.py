from __future__ import annotations

"""Rev G: erase/quench station and one-revolution ghost budget.

Earlier revisions model charge, expose, develop, transfer, fuse, and clean, but
there was no explicit erase/quench station. That is a real electrophotographic
process hole: residual latent charge after transfer/cleaning can re-enter the
next charge cycle as a same-drum-circumference ghost.

This module converts the existing PIDC and station-map math into an executable
requirement:

* a post-cleaning erase source must exist before the next charge station;
* the erase dose must drive a worst-case charged area close to residual voltage;
* the dose must not be an unbounded "blast it with light" value, because high
  erase doses can fatigue an OPC;
* the predicted ghost repeat distance is the drum circumference, so the scanner
  test pattern knows where to look.
"""

import math
from dataclasses import dataclass, asdict

from .engine_math import EngineTargets, line_pitch_mm, process_speed_mm_s
from .pidc_model import model_from_discharge_requirement


@dataclass(frozen=True)
class EraseSpec:
    starting_surface_v: float = -600.0
    target_after_erase_v: float = -80.0
    image_exposure_to_minus_100_uj_cm2: float = 0.45
    erase_design_dose_uj_cm2: float = 0.75
    erase_max_dose_uj_cm2: float = 2.25
    erase_slot_width_mm: float = 5.0
    min_margin_ratio: float = 1.20
    max_overdose_ratio: float = 5.0


def drum_rotation_period_s(target: EngineTargets | None = None) -> float:
    t = target or EngineTargets()
    return math.pi * t.drum_diameter_mm / process_speed_mm_s(t)


def required_erase_energy_uj_cm2(spec: EraseSpec | None = None) -> float:
    s = spec or EraseSpec()
    model = model_from_discharge_requirement(
        s.image_exposure_to_minus_100_uj_cm2,
        v_charge_v=s.starting_surface_v,
        v_discharged_v=-100.0,
        v_residual_v=-60.0,
    )
    return model.exposure_for_potential_uj_cm2(s.target_after_erase_v)


def erase_irradiance_needed_mw_cm2(target: EngineTargets | None = None,
                                   spec: EraseSpec | None = None) -> float:
    """Average irradiance across the erase slot for the design dose.

    1 mW/cm^2 = 0.001 uJ/cm^2 per microsecond.
    """
    t = target or EngineTargets()
    s = spec or EraseSpec()
    dwell_us = s.erase_slot_width_mm / process_speed_mm_s(t) * 1_000_000.0
    return s.erase_design_dose_uj_cm2 / (0.001 * dwell_us)


def ghost_repeat_distance_mm(target: EngineTargets | None = None) -> float:
    t = target or EngineTargets()
    return math.pi * t.drum_diameter_mm


def erase_summary(target: EngineTargets | None = None,
                  spec: EraseSpec | None = None) -> dict:
    t = target or EngineTargets()
    s = spec or EraseSpec()
    required = required_erase_energy_uj_cm2(s)
    margin = s.erase_design_dose_uj_cm2 / required
    overdose = s.erase_design_dose_uj_cm2 / s.image_exposure_to_minus_100_uj_cm2
    line_pitch = line_pitch_mm(t.dpi)
    repeat_mm = ghost_repeat_distance_mm(t)
    return {
        "hypothesis_promoted_to_requirement": "explicit post-cleaning erase/quench station",
        "spec": asdict(s),
        "pre_revG_as_documented": {
            "erase_station_present": False,
            "verdict": "fail_ghost_memory_gate",
            "why": "cleaning blade removes toner but not residual latent charge",
        },
        "revG_requirement": {
            "erase_station_present": True,
            "location": "after cleaning blade and before primary charge roller",
            "required_energy_to_reach_target_uj_cm2": required,
            "design_erase_dose_uj_cm2": s.erase_design_dose_uj_cm2,
            "dose_margin_ratio": margin,
            "over_image_exposure_ratio": overdose,
            "minimum_margin_ratio": s.min_margin_ratio,
            "maximum_allowed_over_image_exposure_ratio": s.max_overdose_ratio,
            "passes_energy_window": margin >= s.min_margin_ratio and overdose <= s.max_overdose_ratio,
            "erase_slot_width_mm": s.erase_slot_width_mm,
            "erase_dwell_ms": s.erase_slot_width_mm / process_speed_mm_s(t) * 1000.0,
            "minimum_average_erase_irradiance_uw_cm2": erase_irradiance_needed_mw_cm2(t, s) * 1000.0,
        },
        "ghost_test_pattern": {
            "predicted_repeat_distance_mm": repeat_mm,
            "predicted_repeat_distance_lines_at_600dpi": repeat_mm / line_pitch,
            "drum_rotation_period_s": drum_rotation_period_s(t),
            "scanner_metric": "print a black/white impulse band, then search one drum circumference downstream for residual contrast",
            "pass_gate": "ghost contrast at one circumference < 1 percent of source-band contrast after erase enabled",
        },
    }
