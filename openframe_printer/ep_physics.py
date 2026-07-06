from __future__ import annotations

from dataclasses import dataclass, asdict
import math

from .engine_math import EngineTargets, process_speed_mm_s


@dataclass(frozen=True)
class ExposureDevelopmentConstraint:
    """Geometry/time budget for OPC exposure-to-development delay.

    This is not an image-quality guarantee. It is a design guardrail: the OPC
    latent image must remain usable between the LED exposure point and the
    developer nip. The actual allowed time comes from the selected OPC's PIDC,
    dark-decay, residual-potential, humidity, and toner/developer behavior.
    """

    target_delay_ms: float
    process_speed_mm_s: float
    max_arc_length_mm: float
    max_angular_separation_deg_for_30mm_drum: float


@dataclass(frozen=True)
class FusingControlPoint:
    """A relative fusing-control proxy from hot-roll fusing dimensional analysis.

    quality_proxy_pt2_over_md is useful only for comparing calibration points
    on the same machine with the same unit conventions. It is not an absolute
    certification or adhesion prediction.
    """

    nip_pressure_kpa: float
    dwell_ms: float
    toner_mass_mg_cm2: float
    toner_particle_diameter_um: float
    surface_temp_c: float
    ambient_c: float
    quality_proxy_pt2_over_md: float
    temperature_ratio_kelvin: float


@dataclass(frozen=True)
class LedShiftBudget:
    led_pixels: int
    line_period_us: float
    single_lane_clock_mhz: float
    dual_lane_clock_mhz: float
    single_lane_shift_time_us: float
    dual_lane_shift_time_us: float
    single_lane_fraction_of_line_period: float
    dual_lane_fraction_of_line_period: float
    minimum_single_lane_clock_mhz_for_25pct_line: float
    minimum_dual_lane_clock_mhz_for_25pct_line: float


def exposure_development_constraint(
    target: EngineTargets | None = None,
    target_delay_ms: float = 50.0,
) -> ExposureDevelopmentConstraint:
    t = target or EngineTargets()
    speed = process_speed_mm_s(t)
    max_arc = speed * target_delay_ms / 1000.0
    circumference = math.pi * t.drum_diameter_mm
    degrees = max_arc / circumference * 360.0
    return ExposureDevelopmentConstraint(
        target_delay_ms=target_delay_ms,
        process_speed_mm_s=speed,
        max_arc_length_mm=max_arc,
        max_angular_separation_deg_for_30mm_drum=degrees,
    )


def led_shift_budget(
    led_pixels: int,
    line_period_us: float,
    clock_mhz: float = 20.0,
) -> LedShiftBudget:
    single_shift_us = led_pixels / clock_mhz
    dual_shift_us = (led_pixels / 2.0) / clock_mhz
    min_single = led_pixels / (line_period_us * 0.25)
    min_dual = (led_pixels / 2.0) / (line_period_us * 0.25)
    return LedShiftBudget(
        led_pixels=led_pixels,
        line_period_us=line_period_us,
        single_lane_clock_mhz=clock_mhz,
        dual_lane_clock_mhz=clock_mhz,
        single_lane_shift_time_us=single_shift_us,
        dual_lane_shift_time_us=dual_shift_us,
        single_lane_fraction_of_line_period=single_shift_us / line_period_us,
        dual_lane_fraction_of_line_period=dual_shift_us / line_period_us,
        minimum_single_lane_clock_mhz_for_25pct_line=min_single,
        minimum_dual_lane_clock_mhz_for_25pct_line=min_dual,
    )


def fusing_control_point(
    nip_pressure_kpa: float,
    dwell_ms: float,
    toner_mass_mg_cm2: float,
    toner_particle_diameter_um: float,
    surface_temp_c: float,
    ambient_c: float = 25.0,
) -> FusingControlPoint:
    # Keep the proxy relative and unit-consistent. Calibration decides its usable range.
    quality_proxy = (nip_pressure_kpa * dwell_ms * dwell_ms) / (
        max(toner_mass_mg_cm2, 1e-9) * max(toner_particle_diameter_um, 1e-9)
    )
    temp_ratio = (surface_temp_c + 273.15) / (ambient_c + 273.15)
    return FusingControlPoint(
        nip_pressure_kpa=nip_pressure_kpa,
        dwell_ms=dwell_ms,
        toner_mass_mg_cm2=toner_mass_mg_cm2,
        toner_particle_diameter_um=toner_particle_diameter_um,
        surface_temp_c=surface_temp_c,
        ambient_c=ambient_c,
        quality_proxy_pt2_over_md=quality_proxy,
        temperature_ratio_kelvin=temp_ratio,
    )


def physics_summary(target: EngineTargets | None = None) -> dict:
    from .engine_math import line_period_us

    t = target or EngineTargets()
    line_period = line_period_us(t)
    shift = led_shift_budget(t.led_pixels, line_period)
    return {
        "led_shift_budget": asdict(shift),
        "exposure_development_constraints": {
            "50ms": asdict(exposure_development_constraint(t, 50.0)),
            "100ms": asdict(exposure_development_constraint(t, 100.0)),
            "200ms": asdict(exposure_development_constraint(t, 200.0)),
        },
        "example_fusing_control_point": asdict(
            fusing_control_point(
                nip_pressure_kpa=350.0,
                dwell_ms=t.fuser_nip_width_mm / process_speed_mm_s(t) * 1000.0,
                toner_mass_mg_cm2=t.toner_dense_black_mg_cm2,
                toner_particle_diameter_um=7.0,
                surface_temp_c=t.nominal_fuser_surface_temp_c,
            )
        ),
        "notes": [
            "20 MHz is not enough to shift 5120 bits inside 25% of the line period on one data lane.",
            "20 MHz is enough for the 25% budget only if the LED bar is split into two 2560-bit data lanes or the clock is raised.",
            "OPC exposure values are tracked in microjoules per square centimeter, not millijoules per square centimeter.",
            "The fusing proxy is comparative only; it must be calibrated with rub/tape/gloss/offset tests.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(physics_summary(), indent=2))
