from __future__ import annotations

from dataclasses import asdict
from .engine_math import EngineTargets, line_pitch_mm, line_rate_lps, line_period_us, led_active_width_mm
from .ep_physics import led_shift_budget


def exposure_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    pitch_um = line_pitch_mm(t.dpi) * 1000.0
    period_us = line_period_us(t)
    shift = led_shift_budget(t.led_pixels, period_us, clock_mhz=20.0)
    return {
        "target": asdict(t),
        "technology": "single-pass stationary LED exposure bar",
        "led_pixels": t.led_pixels,
        "pixel_pitch_um": pitch_um,
        "active_width_mm": led_active_width_mm(t),
        "line_rate_lps": line_rate_lps(t),
        "line_period_us": period_us,
        "line_payload_bytes_1bpp": t.led_pixels // 8,
        "single_lane_shift_time_us_at_20mhz": shift.single_lane_shift_time_us,
        "dual_lane_shift_time_us_at_20mhz": shift.dual_lane_shift_time_us,
        "single_lane_fraction_of_line_period_at_20mhz": shift.single_lane_fraction_of_line_period,
        "dual_lane_fraction_of_line_period_at_20mhz": shift.dual_lane_fraction_of_line_period,
        "minimum_single_lane_clock_mhz_for_25pct_line_time": shift.minimum_single_lane_clock_mhz_for_25pct_line,
        "minimum_dual_lane_clock_mhz_for_25pct_line_time": shift.minimum_dual_lane_clock_mhz_for_25pct_line,
        "recommended_shift_clock_mhz_revB": 20.0,
        "recommended_data_lanes_revB": 2,
        "exposure_wavelength_nm_initial": 780,
        "exposure_energy_sweep_uJ_cm2": [0.15, 0.25, 0.35, 0.45, 0.60, 0.80, 1.00],
        "initial_nominal_exposure_uJ_cm2": 0.45,
        "line_memory_strategy": "two 640-byte line buffers ping-ponged by DMA/PIO; use two physical LED data lanes or raise single-lane clock above 30 MHz",
    }


def led_group_map(target: EngineTargets | None = None, group_size: int = 64) -> list[dict]:
    t = target or EngineTargets()
    rows = []
    for group_index, first in enumerate(range(0, t.led_pixels, group_size)):
        last = min(first + group_size - 1, t.led_pixels - 1)
        rows.append({
            "group": group_index,
            "first_pixel": first,
            "last_pixel": last,
            "pixels": last - first + 1,
            "first_x_mm": round(first * line_pitch_mm(t.dpi), 4),
            "last_x_mm": round(last * line_pitch_mm(t.dpi), 4),
            "payload_byte_start": first // 8,
            "payload_byte_end": last // 8,
        })
    return rows


if __name__ == "__main__":
    import json
    print(json.dumps(exposure_summary(), indent=2))
