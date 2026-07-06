from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from .engine_math import EngineTargets, process_speed_mm_s, line_period_us


STATIONS_MM = {
    "tray_leading_edge_home": 0.0,
    "pickup_nip": 25.0,
    "separation_nip": 32.0,
    "pre_registration_sensor": 88.0,
    "registration_nip": 112.0,
    "image_sync_sensor": 138.0,
    "transfer_nip": 180.0,
    "fuser_entry": 255.0,
    "fuser_exit": 285.0,
    "exit_sensor": 340.0,
    "output_roller": 360.0,
}


@dataclass(frozen=True)
class MotionConfig:
    registration_hold_ms: float = 120.0
    jam_window_fraction: float = 0.20
    full_steps_per_rev: int = 200
    microsteps: int = 16
    pickup_gear_ratio: float = 1.0
    registration_gear_ratio: float = 1.0
    fuser_gear_ratio: float = 1.0


def stepper_rate_hz(surface_speed_mm_s: float, roller_diameter_mm: float, gear_ratio: float, full_steps: int, microsteps: int) -> float:
    roller_rps = surface_speed_mm_s / (math.pi * roller_diameter_mm)
    return roller_rps * gear_ratio * full_steps * microsteps


def transit_events(target: EngineTargets | None = None, cfg: MotionConfig | None = None) -> dict:
    t = target or EngineTargets()
    c = cfg or MotionConfig()
    speed = process_speed_mm_s(t)
    events = []
    for name, y in STATIONS_MM.items():
        nominal_ms = y / speed * 1000.0
        if y >= STATIONS_MM["registration_nip"]:
            nominal_ms += c.registration_hold_ms
        events.append({
            "station": name,
            "y_mm": y,
            "lead_edge_nominal_ms_from_pick_start": nominal_ms,
            "early_fault_ms": nominal_ms * (1.0 - c.jam_window_fraction),
            "late_fault_ms": nominal_ms * (1.0 + c.jam_window_fraction),
        })
    return {
        "target": asdict(t),
        "motion_config": asdict(c),
        "process_speed_mm_s": speed,
        "line_period_us": line_period_us(t),
        "events": events,
        "stepper_rates_hz": {
            "pickup_roller": stepper_rate_hz(speed, t.pickup_roller_diameter_mm, c.pickup_gear_ratio, c.full_steps_per_rev, c.microsteps),
            "registration_roller": stepper_rate_hz(speed, t.registration_roller_diameter_mm, c.registration_gear_ratio, c.full_steps_per_rev, c.microsteps),
            "fuser_hot_roller": stepper_rate_hz(speed, t.fuser_hot_roller_diameter_mm, c.fuser_gear_ratio, c.full_steps_per_rev, c.microsteps),
            "exit_roller": stepper_rate_hz(speed, t.exit_roller_diameter_mm, 1.0, c.full_steps_per_rev, c.microsteps),
        },
        "registration_to_transfer_mm": STATIONS_MM["transfer_nip"] - STATIONS_MM["registration_nip"],
        "image_sync_to_transfer_lines": round((STATIONS_MM["transfer_nip"] - STATIONS_MM["image_sync_sensor"]) / (25.4 / t.dpi)),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(transit_events(), indent=2))
