from __future__ import annotations

"""Rev G: emissions containment budget for toner/fuser/open-frame safety.

This is not a health certification model. It is an engineering gate that keeps
OpenFrame from pretending a laser/LED EP printer can be literally open around
paper exit, fuser, toner, and fan paths. The output is deliberately framed as a
qualification requirement: measure the real machine, but do not ship a chassis
that has no defined capture path.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class EmissionCase:
    name: str
    particle_emission_per_min: float
    room_volume_m3: float = 30.0
    room_air_changes_per_hour: float = 4.0
    source_capture_efficiency: float = 0.0
    output_tray_capture_efficiency: float = 0.0


def steady_state_particles_per_m3(case: EmissionCase) -> float:
    removal_per_min = case.room_air_changes_per_hour / 60.0
    if removal_per_min <= 0 or case.room_volume_m3 <= 0:
        raise ValueError("room volume and air change rate must be positive")
    uncaptured_fraction = 1.0 - min(1.0, max(0.0, case.source_capture_efficiency + case.output_tray_capture_efficiency))
    return case.particle_emission_per_min * uncaptured_fraction / (removal_per_min * case.room_volume_m3)


def evaluate_emission_case(case: EmissionCase) -> dict:
    concentration = steady_state_particles_per_m3(case)
    # Internal engineering threshold, not a legal exposure limit. It forces a
    # bench test before calling the chassis safe for home-office use.
    review_threshold = 1.0e10
    return {
        **asdict(case),
        "modeled_steady_state_particles_per_m3": concentration,
        "internal_review_threshold_particles_per_m3": review_threshold,
        "passes_internal_review_threshold": concentration <= review_threshold,
        "verdict": "bench_emissions_test_required" if concentration > review_threshold else "capture_design_plausible_pending_test",
    }


def emissions_summary() -> dict:
    cases = [
        EmissionCase("low_emitter_uncontained", 1.0e8),
        EmissionCase("high_emitter_uncontained", 1.0e12),
        EmissionCase("high_emitter_fan_filter_only", 1.0e12, source_capture_efficiency=0.90, output_tray_capture_efficiency=0.0),
        EmissionCase("high_emitter_source_plus_output_capture", 1.0e12, source_capture_efficiency=0.90, output_tray_capture_efficiency=0.09),
    ]
    evaluated = [evaluate_emission_case(c) for c in cases]
    return {
        "requirement": "negative-pressure fuser/exit enclosure plus measured particle/ozone qualification",
        "not_a_health_certification": True,
        "source_range_particles_per_min": [1.0e8, 1.0e12],
        "cases": evaluated,
        "fan_filter_only_is_not_enough_for_high_emitter": not next(c for c in evaluated if c["name"] == "high_emitter_fan_filter_only")["passes_internal_review_threshold"],
        "output_tray_capture_changes_verdict": next(c for c in evaluated if c["name"] == "high_emitter_source_plus_output_capture")["passes_internal_review_threshold"],
        "hardware_delta": "do not leave paper exit as an uncontrolled plume; route fuser/exit leakage through serviceable filter path and test with real toner/paper",
    }
