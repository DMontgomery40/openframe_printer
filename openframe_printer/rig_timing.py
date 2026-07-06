from __future__ import annotations

from dataclasses import dataclass, asdict
import math

from .engine_math import EngineTargets, line_period_us, lines_down, process_speed_mm_s

# Station Y positions from tray lip, per docs/04_mechanics_paper_path.md.
STATION_POSITIONS_MM = {
    "pickup": 25.0,
    "separation": 31.0,
    "registration": 105.0,
    "transfer": 175.0,
    "fuser": 260.0,
    "exit": 340.0,
}

# Jam window tolerance: a sheet edge arriving outside +/- this fraction of the
# expected transit time is declared a feed fault on the motion rig.
TRANSIT_TOLERANCE = 0.20


@dataclass(frozen=True)
class StepperConfig:
    full_steps_per_rev: int = 200
    microsteps: int = 16
    gear_ratio: float = 1.0  # motor revs per roller rev


def transit_windows_ms(target: EngineTargets) -> dict:
    """Expected sensor-to-sensor transit times with jam-detection windows."""
    speed = process_speed_mm_s(target)
    names = list(STATION_POSITIONS_MM)
    windows = {}
    for a, b in zip(names, names[1:]):
        distance = STATION_POSITIONS_MM[b] - STATION_POSITIONS_MM[a]
        nominal = distance / speed * 1000.0
        windows[f"{a}_to_{b}"] = {
            "distance_mm": distance,
            "nominal_ms": nominal,
            "early_fault_ms": nominal * (1.0 - TRANSIT_TOLERANCE),
            "late_fault_ms": nominal * (1.0 + TRANSIT_TOLERANCE),
        }
    return windows


def stepper_rate_hz(process_speed: float, roller_diameter_mm: float, cfg: StepperConfig) -> float:
    roller_rps = process_speed / (math.pi * roller_diameter_mm)
    return roller_rps * cfg.gear_ratio * cfg.full_steps_per_rev * cfg.microsteps


def naive_strobe_drift_lines(target: EngineTargets, timer_tick_us: float = 1.0) -> float:
    """Cumulative line drift over one Letter page if the line period is rounded
    once to the timer tick and replayed verbatim every line."""
    ideal = line_period_us(target)
    rounded = round(ideal / timer_tick_us) * timer_tick_us
    lines = lines_down(target.letter_length_mm, target.dpi)
    return abs(rounded - ideal) * lines / ideal


def accumulator_strobe_drift_lines(target: EngineTargets, timer_tick_us: float = 1.0) -> float:
    """Worst-case line drift with a fractional phase accumulator: the scheduled
    strobe never departs from ideal time by more than one timer tick."""
    return timer_tick_us / line_period_us(target)


def rig_plan(target: EngineTargets | None = None, cfg: StepperConfig | None = None) -> dict:
    t = target or EngineTargets()
    c = cfg or StepperConfig()
    speed = process_speed_mm_s(t)
    drift_budget_lines = 0.5  # NEXT.md Step 4 pass/fail
    naive_drift = naive_strobe_drift_lines(t)
    accum_drift = accumulator_strobe_drift_lines(t)
    return {
        "target": asdict(t),
        "stepper": asdict(c),
        "process_speed_mm_s": speed,
        "station_positions_mm": STATION_POSITIONS_MM,
        "transit_windows_ms": transit_windows_ms(t),
        "stepper_rates_hz": {
            "pickup": stepper_rate_hz(speed, t.roller_pickup_diameter_mm, c),
            "registration": stepper_rate_hz(speed, t.roller_registration_diameter_mm, c),
            "fuser": stepper_rate_hz(speed, t.roller_fuser_diameter_mm, c),
        },
        "line_strobe": {
            "line_period_us": line_period_us(t),
            "timer_tick_us": 1.0,
            "drift_budget_lines": drift_budget_lines,
            "naive_rounded_period_drift_lines_per_page": naive_drift,
            "naive_rounded_period_passes": naive_drift <= drift_budget_lines,
            "phase_accumulator_drift_lines_max": accum_drift,
            "phase_accumulator_passes": accum_drift <= drift_budget_lines,
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(rig_plan(EngineTargets(dpi=600, ppm=12)), indent=2))
