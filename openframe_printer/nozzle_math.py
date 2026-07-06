from __future__ import annotations

from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class InkjetNozzleTargets:
    revision: str = "IJ-RD0"
    dpi: int = 600
    nozzle_diameter_um: float = 24.0
    nozzle_pitch_um: float = 42.3333333333
    drop_volume_pl: float = 10.0
    drop_velocity_m_s: float = 7.0
    max_fire_frequency_hz: float = 12000.0
    ink_viscosity_mpa_s: float = 3.0
    ink_surface_tension_mn_m: float = 32.0
    ink_density_kg_m3: float = 1000.0
    chamber_length_um: float = 55.0
    chamber_width_um: float = 45.0
    chamber_height_um: float = 28.0


def droplet_diameter_um(volume_pl: float) -> float:
    # 1 pL = 1e-15 m^3. Sphere diameter = cbrt(6V/pi).
    volume_m3 = volume_pl * 1e-15
    return ((6.0 * volume_m3 / math.pi) ** (1.0 / 3.0)) * 1e6


def reynolds_number(t: InkjetNozzleTargets) -> float:
    rho = t.ink_density_kg_m3
    v = t.drop_velocity_m_s
    d = t.nozzle_diameter_um * 1e-6
    mu = t.ink_viscosity_mpa_s * 1e-3
    return rho * v * d / mu


def weber_number(t: InkjetNozzleTargets) -> float:
    rho = t.ink_density_kg_m3
    v = t.drop_velocity_m_s
    d = t.nozzle_diameter_um * 1e-6
    sigma = t.ink_surface_tension_mn_m * 1e-3
    return rho * v * v * d / sigma


def nozzle_summary(target: InkjetNozzleTargets | None = None) -> dict:
    t = target or InkjetNozzleTargets()
    return {
        "target": asdict(t),
        "droplet_diameter_um_for_target_volume": droplet_diameter_um(t.drop_volume_pl),
        "pixel_pitch_um": 25_400.0 / t.dpi,
        "nozzle_pitch_um": t.nozzle_pitch_um,
        "reynolds_number": reynolds_number(t),
        "weber_number": weber_number(t),
        "single_nozzle_flow_ul_min_at_max_frequency": t.drop_volume_pl * t.max_fire_frequency_hz * 60.0 / 1_000_000.0,
        "array_1024_nozzle_flow_ml_min_at_max_frequency": t.drop_volume_pl * t.max_fire_frequency_hz * 60.0 * 1024.0 / 1_000_000_000.0,
        "recommended_rd_path": "piezo drop-on-demand test chip before thermal bubble nozzles",
        "why_not_first_product": "nozzle fabrication, ink chemistry, drying, purge, capping, and satellite drops dominate the risk",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(nozzle_summary(), indent=2))
