from __future__ import annotations

"""Rev G: registration, skew, and LED-width margin budget.

Rev E made OFP1 deterministic, but deterministic bytes do not make a page land
on paper. The old docs claimed the 5120-pixel bar provides registration slack;
this module checks that claim against the 600 dpi pitch and page width.
"""

import math
from dataclasses import dataclass, asdict

from .engine_math import EngineTargets, led_active_width_mm, line_period_us, line_pitch_mm, process_speed_mm_s


@dataclass(frozen=True)
class RegistrationSpec:
    print_quality_start_tolerance_mm: float = 0.25
    old_test_plan_registration_tolerance_mm: float = 1.0
    desired_lateral_slack_each_side_mm: float = 1.0
    current_led_pixels: int = 5120
    proposed_led_pixels_byte_aligned: int = 5184


def timing_error_for_mm(target: EngineTargets, error_mm: float) -> dict:
    pitch = line_pitch_mm(target.dpi)
    return {
        "error_mm": error_mm,
        "error_lines": error_mm / pitch,
        "error_ms": error_mm / process_speed_mm_s(target) * 1000.0,
    }


def led_width_for_pixels(target: EngineTargets, pixels: int) -> float:
    return pixels * line_pitch_mm(target.dpi)


def minimum_pixels_for_lateral_slack(target: EngineTargets, slack_each_side_mm: float) -> int:
    required_width = target.page_width_mm + 2.0 * slack_each_side_mm
    return math.ceil(required_width / line_pitch_mm(target.dpi))


def round_up_to_byte_aligned_pixels(pixels: int, byte_group: int = 64) -> int:
    return int(math.ceil(pixels / byte_group) * byte_group)


def registration_summary(target: EngineTargets | None = None,
                         spec: RegistrationSpec | None = None) -> dict:
    t = target or EngineTargets()
    s = spec or RegistrationSpec()
    current_width = led_active_width_mm(t)
    current_slack_each = (current_width - t.page_width_mm) / 2.0
    min_pixels = minimum_pixels_for_lateral_slack(t, s.desired_lateral_slack_each_side_mm)
    rounded = round_up_to_byte_aligned_pixels(min_pixels)
    proposed_width = led_width_for_pixels(t, s.proposed_led_pixels_byte_aligned)
    old = timing_error_for_mm(t, s.old_test_plan_registration_tolerance_mm)
    quality = timing_error_for_mm(t, s.print_quality_start_tolerance_mm)
    skew_angle_old_deg = math.degrees(math.atan2(s.old_test_plan_registration_tolerance_mm, t.page_width_mm))
    return {
        "requirement": "OFP1 line determinism plus mechanical registration tolerance budget",
        "spec": asdict(s),
        "line_pitch_mm": line_pitch_mm(t.dpi),
        "line_period_us": line_period_us(t),
        "current_5120_bar": {
            "active_width_mm": current_width,
            "total_width_margin_mm": current_width - t.page_width_mm,
            "lateral_slack_each_side_mm": current_slack_each,
            "slack_pixels_each_side": current_slack_each / line_pitch_mm(t.dpi),
            "passes_1mm_each_side_slack_goal": current_slack_each >= s.desired_lateral_slack_each_side_mm,
        },
        "old_test_plan_plus_minus_1mm": {
            **old,
            "verdict": "jam_timing_only_not_print_quality",
            "reason": "+/-1 mm is over 23 lines at 600 dpi and exceeds current LED edge slack",
        },
        "print_quality_start_gate": quality,
        "skew_budget": {
            "old_1mm_across_page_skew_angle_deg": skew_angle_old_deg,
            "old_1mm_skew_line_delta_across_width": s.old_test_plan_registration_tolerance_mm / line_pitch_mm(t.dpi),
            "first_build_quality_skew_limit_mm_across_width": s.print_quality_start_tolerance_mm,
        },
        "recommended_revG_LED_or_margins": {
            "minimum_pixels_for_1mm_each_side_slack": min_pixels,
            "byte_aligned_pixels_for_1mm_each_side_slack": rounded,
            "proposed_led_pixels": s.proposed_led_pixels_byte_aligned,
            "proposed_active_width_mm": proposed_width,
            "proposed_lateral_slack_each_side_mm": (proposed_width - t.page_width_mm) / 2.0,
            "raw_data_rate_multiplier_vs_5120": s.proposed_led_pixels_byte_aligned / s.current_led_pixels,
            "alternative": "keep 5120 pixels only if guaranteed printable width is reduced to 214 mm or lateral registration is proven below +/-0.25 mm",
        },
    }
