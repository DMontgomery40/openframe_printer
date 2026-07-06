from __future__ import annotations

"""Rev G LED-bar optical spot / MTF budget.

Previous revisions treated 600 dpi as an electrical pixel count. A real LED
bar can have the right number of emitters and still smear the latent image if
the lens/spot blur is too wide. This module models the latent-image optical
transfer as a Gaussian spot and turns the 600 dpi requirement into an RFQ gate:
MTF at the 600 dpi Nyquist frequency, plus neighboring-pixel crosstalk.
"""

import math

from .engine_math import EngineTargets, line_pitch_mm


def nyquist_lp_per_mm(target: EngineTargets | None = None) -> float:
    t = target or EngineTargets()
    return 1.0 / (2.0 * line_pitch_mm(t.dpi))


def gaussian_mtf(fwhm_um: float, spatial_frequency_lp_per_mm: float) -> float:
    sigma_mm = (fwhm_um / 1000.0) / 2.354820045
    return math.exp(-2.0 * math.pi * math.pi * sigma_mm * sigma_mm * spatial_frequency_lp_per_mm * spatial_frequency_lp_per_mm)


def fwhm_for_mtf(target_mtf: float, spatial_frequency_lp_per_mm: float) -> float:
    sigma_mm = math.sqrt(-math.log(target_mtf) / (2.0 * math.pi * math.pi * spatial_frequency_lp_per_mm * spatial_frequency_lp_per_mm))
    return sigma_mm * 2.354820045 * 1000.0


def neighbor_crosstalk_at_one_pixel(fwhm_um: float, target: EngineTargets | None = None) -> float:
    t = target or EngineTargets()
    sigma_um = fwhm_um / 2.354820045
    pitch_um = line_pitch_mm(t.dpi) * 1000.0
    return math.exp(-(pitch_um * pitch_um) / (2.0 * sigma_um * sigma_um))


def optical_case(fwhm_um: float, target: EngineTargets | None = None, mtf_gate: float = 0.35, crosstalk_gate: float = 0.15) -> dict:
    t = target or EngineTargets()
    freq = nyquist_lp_per_mm(t)
    mtf = gaussian_mtf(fwhm_um, freq)
    crosstalk = neighbor_crosstalk_at_one_pixel(fwhm_um, t)
    return {
        "spot_fwhm_um": fwhm_um,
        "nyquist_lp_per_mm": freq,
        "mtf_at_600dpi_nyquist": mtf,
        "neighbor_pixel_crosstalk_fraction": crosstalk,
        "passes_mtf_gate": mtf >= mtf_gate,
        "passes_crosstalk_gate": crosstalk <= crosstalk_gate,
        "passes_revG_optical_gate": mtf >= mtf_gate and crosstalk <= crosstalk_gate,
    }


def optical_mtf_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    freq = nyquist_lp_per_mm(t)
    mtf_gate = 0.35
    max_fwhm = fwhm_for_mtf(mtf_gate, freq)
    cases = [optical_case(f, t, mtf_gate=mtf_gate) for f in (35.0, 40.0, 45.0, 50.0, 60.0, 85.0)]
    return {
        "revision": "M1-REV-G",
        "finding": "The LED bar RFQ needs an optical MTF/spot gate; emitter count and shift timing alone do not prove 600 dpi latent-image contrast.",
        "dpi": t.dpi,
        "pixel_pitch_um": line_pitch_mm(t.dpi) * 1000.0,
        "nyquist_lp_per_mm": freq,
        "required_mtf_at_nyquist": mtf_gate,
        "max_gaussian_spot_fwhm_um_for_mtf_gate": max_fwhm,
        "neighbor_crosstalk_gate_fraction": 0.15,
        "cases": cases,
        "rfq_requirement": "Supplier must provide measured MTF >= 0.35 at 12 lp/mm at the OPC plane, or equivalent measured spot FWHM <= 45 um with crosstalk <= 15% at one-pixel spacing.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(optical_mtf_summary(), indent=2))
