from __future__ import annotations

"""Rev G motion-registration and line-pitch error budget.

The electrophotographic process does not care that a stepper was commanded at
62 mm/s; it cares where the drum surface actually is when the LED line fires.
This module quantifies open-loop process-speed error in lines, then sizes an
encoder-based line clock and registration timestamp budget.
"""

from dataclasses import dataclass, asdict
import math

from .engine_math import EngineTargets, line_pitch_mm, process_speed_mm_s


@dataclass(frozen=True)
class EncoderSpec:
    name: str
    cpr: int
    quadrature_edges_per_cycle: int = 4
    interpolation: int = 1


def open_loop_scale_error(target: EngineTargets | None = None, speed_error_fraction: float = 0.005) -> dict:
    t = target or EngineTargets()
    page_mm = t.letter_length_mm
    pitch = line_pitch_mm(t.dpi)
    error_mm = page_mm * speed_error_fraction
    return {
        "speed_error_fraction": speed_error_fraction,
        "page_length_mm": page_mm,
        "line_pitch_mm": pitch,
        "page_scale_error_mm": error_mm,
        "page_scale_error_lines": error_mm / pitch,
        "verdict": "fail" if abs(error_mm / pitch) > 1.0 else "pass",
    }


def encoder_resolution(spec: EncoderSpec, target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    circumference = math.pi * t.drum_diameter_mm
    pitch = line_pitch_mm(t.dpi)
    physical_edges = spec.cpr * spec.quadrature_edges_per_cycle
    effective_edges = physical_edges * spec.interpolation
    edge_pitch_mm = circumference / effective_edges
    return {
        "spec": asdict(spec),
        "drum_circumference_mm": circumference,
        "line_pitch_mm": pitch,
        "physical_edges_per_rev": physical_edges,
        "effective_edges_per_rev": effective_edges,
        "edge_pitch_um": edge_pitch_mm * 1000.0,
        "edge_pitch_lines": edge_pitch_mm / pitch,
        "passes_quarter_line_quantization_gate": edge_pitch_mm <= 0.25 * pitch,
    }


def sensor_timestamp_error(target: EngineTargets | None = None, timestamp_jitter_us: float = 150.0) -> dict:
    t = target or EngineTargets()
    speed = process_speed_mm_s(t)
    error_mm = speed * timestamp_jitter_us / 1_000_000.0
    pitch = line_pitch_mm(t.dpi)
    return {
        "timestamp_jitter_us": timestamp_jitter_us,
        "process_speed_mm_s": speed,
        "registration_position_error_um": error_mm * 1000.0,
        "registration_error_lines": error_mm / pitch,
        "passes_quarter_line_gate": error_mm <= 0.25 * pitch,
    }


def motion_registration_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    options = [
        encoder_resolution(EncoderSpec("1024_cpr_quadrature_no_interp", 1024), t),
        encoder_resolution(EncoderSpec("2048_cpr_quadrature_no_interp", 2048), t),
        encoder_resolution(EncoderSpec("4096_cpr_quadrature_no_interp", 4096), t),
        encoder_resolution(EncoderSpec("2048_cpr_quadrature_4x_timer_interp", 2048, interpolation=4), t),
    ]
    recommended = next(o for o in options if o["spec"]["name"] == "4096_cpr_quadrature_no_interp")
    return {
        "revision": "M1-REV-G",
        "finding": "Open-loop process speed is not a line-placement proof; a 0.5% speed error stretches Letter by about 33 lines.",
        "line_pitch_um": line_pitch_mm(t.dpi) * 1000.0,
        "process_speed_mm_s": process_speed_mm_s(t),
        "open_loop_cases": [
            open_loop_scale_error(t, 0.001),
            open_loop_scale_error(t, 0.005),
            open_loop_scale_error(t, 0.010),
        ],
        "encoder_options": options,
        "recommended_encoder": recommended,
        "registration_sensor_cases": [
            sensor_timestamp_error(t, 50.0),
            sensor_timestamp_error(t, 150.0),
            sensor_timestamp_error(t, 300.0),
        ],
        "revG_motion_contract": "LED line firing is slaved to a drum encoder; paper registration sensor only sets image phase/lead-edge offset, not continuous line spacing.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(motion_registration_summary(), indent=2))
