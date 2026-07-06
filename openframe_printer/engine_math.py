from __future__ import annotations

from dataclasses import dataclass, asdict
import math

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class EngineTargets:
    """OpenFrame M1 Rev A baseline constants.

    These are not copied from a donor printer. They are the first self-consistent
    dimensions for a new monochrome LED electrophotographic engine.
    """

    revision: str = "M1-REV-A"
    page_width_mm: float = 216.0
    letter_length_mm: float = 279.4
    a4_length_mm: float = 297.0
    inter_page_gap_mm: float = 30.6
    dpi: int = 600
    ppm: int = 12
    led_pixels: int = 5120
    drum_diameter_mm: float = 30.0
    drum_wall_clearance_mm: float = 2.0
    transfer_roller_diameter_mm: float = 14.0
    developer_roller_diameter_mm: float = 16.0
    primary_charge_roller_diameter_mm: float = 10.0
    pickup_roller_diameter_mm: float = 18.0
    registration_roller_diameter_mm: float = 12.0
    exit_roller_diameter_mm: float = 16.0
    fuser_hot_roller_diameter_mm: float = 24.0
    fuser_pressure_roller_diameter_mm: float = 24.0
    fuser_nip_width_mm: float = 5.0
    toner_dense_black_mg_cm2: float = 0.55
    nominal_fuser_surface_temp_c: float = 178.0


def process_speed_mm_s(target: EngineTargets, page_length_mm: float | None = None) -> float:
    length = target.letter_length_mm if page_length_mm is None else page_length_mm
    return (length + target.inter_page_gap_mm) * target.ppm / 60.0


def line_pitch_mm(dpi: int) -> float:
    return MM_PER_INCH / dpi


def line_rate_lps(target: EngineTargets, page_length_mm: float | None = None) -> float:
    return process_speed_mm_s(target, page_length_mm) / line_pitch_mm(target.dpi)


def line_period_us(target: EngineTargets, page_length_mm: float | None = None) -> float:
    return 1_000_000.0 / line_rate_lps(target, page_length_mm)


def pixels_across(width_mm: float, dpi: int) -> int:
    return round(width_mm / MM_PER_INCH * dpi)


def lines_down(length_mm: float, dpi: int) -> int:
    return round(length_mm / MM_PER_INCH * dpi)


def page_bytes(width_px: int, height_lines: int) -> int:
    return ((width_px + 7) // 8) * height_lines


def roller_rpm(surface_speed_mm_s: float, diameter_mm: float) -> float:
    return surface_speed_mm_s / (math.pi * diameter_mm) * 60.0


def led_active_width_mm(target: EngineTargets) -> float:
    return target.led_pixels * line_pitch_mm(target.dpi)


def pixel_area_mm2(target: EngineTargets) -> float:
    p = line_pitch_mm(target.dpi)
    return p * p


def page_image_area_cm2(target: EngineTargets, page_length_mm: float | None = None) -> float:
    length = target.letter_length_mm if page_length_mm is None else page_length_mm
    return (target.page_width_mm * length) / 100.0


def dense_black_toner_per_page_g(target: EngineTargets, coverage: float = 0.05) -> float:
    """Approximate toner mass for coverage fraction.

    0.05 means normal office page coverage, not solid black page.
    """
    return page_image_area_cm2(target) * coverage * target.toner_dense_black_mg_cm2 / 1000.0


def fuser_dwell_ms(target: EngineTargets) -> float:
    return target.fuser_nip_width_mm / process_speed_mm_s(target) * 1000.0


def design_calcs(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    speed = process_speed_mm_s(t)
    letter_lines = lines_down(t.letter_length_mm, t.dpi)
    a4_lines = lines_down(t.a4_length_mm, t.dpi)
    page_width_px = pixels_across(t.page_width_mm, t.dpi)
    led_width_mm = led_active_width_mm(t)
    return {
        "target": asdict(t),
        "process_speed_mm_s_letter": speed,
        "process_speed_mm_s_a4": process_speed_mm_s(t, t.a4_length_mm),
        "line_pitch_mm": line_pitch_mm(t.dpi),
        "line_pitch_um": line_pitch_mm(t.dpi) * 1000.0,
        "line_rate_lps_letter": line_rate_lps(t),
        "line_period_us_letter": line_period_us(t),
        "page_width_pixels_at_600dpi": page_width_px,
        "led_pixels": t.led_pixels,
        "led_line_payload_bytes": page_bytes(t.led_pixels, 1),
        "led_active_width_mm": led_width_mm,
        "led_width_margin_mm_total": led_width_mm - t.page_width_mm,
        "letter_height_lines": letter_lines,
        "a4_height_lines": a4_lines,
        "raw_letter_page_bytes_1bpp_using_led_width": page_bytes(t.led_pixels, letter_lines),
        "raw_a4_page_bytes_1bpp_using_led_width": page_bytes(t.led_pixels, a4_lines),
        "raw_data_rate_mbit_s": t.led_pixels * line_rate_lps(t) / 1_000_000.0,
        "drum_circumference_mm": math.pi * t.drum_diameter_mm,
        "drum_rpm": roller_rpm(speed, t.drum_diameter_mm),
        "drum_rotations_per_letter_page_plus_gap": (t.letter_length_mm + t.inter_page_gap_mm) / (math.pi * t.drum_diameter_mm),
        "primary_charge_roller_rpm": roller_rpm(speed, t.primary_charge_roller_diameter_mm),
        "developer_roller_rpm_nominal_same_surface_speed": roller_rpm(speed, t.developer_roller_diameter_mm),
        "transfer_roller_rpm": roller_rpm(speed, t.transfer_roller_diameter_mm),
        "pickup_roller_rpm_at_process_speed": roller_rpm(speed, t.pickup_roller_diameter_mm),
        "registration_roller_rpm_at_process_speed": roller_rpm(speed, t.registration_roller_diameter_mm),
        "fuser_hot_roller_rpm": roller_rpm(speed, t.fuser_hot_roller_diameter_mm),
        "exit_roller_rpm": roller_rpm(speed, t.exit_roller_diameter_mm),
        "fuser_nip_dwell_ms": fuser_dwell_ms(t),
        "toner_per_letter_page_5pct_coverage_g": dense_black_toner_per_page_g(t, 0.05),
        "toner_per_letter_page_100pct_solid_g": dense_black_toner_per_page_g(t, 1.0),
        "first_prototype_prints_per_80g_toner_at_5pct": 80.0 / dense_black_toner_per_page_g(t, 0.05),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(design_calcs(), indent=2))
