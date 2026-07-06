from __future__ import annotations

"""Rev C/D electrostatic voltage ladder.

The package has always carried an HV bias table, but nothing ever connected
the rungs: what surface potential the PCR bias actually produces, what the
LED exposure leaves behind, and whether the developer bias then sits in a
working window. This module builds that ladder and checks it end to end.

Doing so exposes a fundamental Rev A inconsistency that survived both prior
research passes:

    A DC-biased contact charge roller does not transfer its bias voltage to
    the drum. Charging happens by air-gap discharge, which only begins once
    the applied bias exceeds a threshold; above it, the surface potential
    tracks applied bias MINUS that threshold (the classic DC contact-charging
    relation, V_s ~ V_applied - V_th, with V_th ~ 500-650 V for typical OPC
    dielectric stacks -- Paschen-gap behavior).

    Rev A commands PCR_CHARGE = -720 V and simultaneously assumes a -600 V
    charged drum (the whole 0.15-0.80 uJ/cm^2 exposure story discharges
    "-600 V to -100 V"). With V_th in the plausible band, -720 V of DC bias
    yields roughly -70 to -220 V of drum surface. The developer bias (-320 V)
    would then sit BELOW the unexposed surface potential: the background
    field reverses and the page tones everywhere. Rev A as tabled cannot
    print.

Rev C offers the two standard fixes as concrete channel proposals:

  Option A (DC-only): raise PCR bias to ~ -(|V_0| + V_th) = about -1180 V
            nominal, with the monitor watching for the discharge knee.
  Option B (AC+DC):   DC component equal to the target surface potential
            (-600 V) plus an AC component with peak-to-peak >= 2 x V_th
            (>= ~1.7 kVpp); the AC discharge averages the surface to the DC
            value. Costs an AC HV stage; buys charge uniformity and
            insensitivity to V_th drift.

Every number here is a model with stated assumptions, not a measurement. The
ladder's job is self-consistency: it catches designs whose own numbers
cannot coexist, which is exactly what happened to Rev A.
"""

from dataclasses import dataclass, asdict

from .pidc_model import PidcModel, model_from_discharge_requirement

# Plausible DC contact-charging threshold band for organic photoconductor
# stacks (dielectric thickness dependent). Treated as an uncertainty band,
# not a constant.
V_TH_NOMINAL_V = 560.0
V_TH_BAND_V = (500.0, 650.0)
# About 2 * max(Vth) is the theoretical peak-to-peak AC threshold-band floor.
# Rev D keeps the physics floor visible but specs the hardware with headroom so
# the generated voltage ladder and the generated HV channel table cannot drift.
AC_CHARGE_PHYSICS_MIN_KVPP = round(2.0 * V_TH_BAND_V[1] / 1000.0, 2)
AC_CHARGE_SPEC_KVPP = 1.7

# Working-window floors used by the ladder verdicts. These are design floors
# for a first build, not universal constants.
MIN_DEVELOPMENT_CONTRAST_V = 150.0
MIN_FOG_MARGIN_V = 100.0


def dc_roller_surface_potential_v(applied_v: float, threshold_v: float = V_TH_NOMINAL_V) -> float:
    """DC contact-charging approximation: no charging below threshold, then
    the surface tracks applied bias minus threshold (magnitude)."""
    magnitude = abs(applied_v)
    if magnitude <= threshold_v:
        return 0.0
    surface = magnitude - threshold_v
    return -surface if applied_v < 0.0 else surface


def dc_bias_for_surface_potential_v(target_surface_v: float, threshold_v: float = V_TH_NOMINAL_V) -> float:
    magnitude = abs(target_surface_v) + threshold_v
    return -magnitude if target_surface_v < 0.0 else magnitude


@dataclass(frozen=True)
class LadderRungs:
    pcr_applied_v: float
    charged_surface_v: float
    exposure_uj_cm2: float
    latent_surface_v: float
    developer_bias_v: float
    development_contrast_v: float  # developer bias minus latent surface (drives toner to image)
    fog_margin_v: float            # charged surface minus developer bias (holds toner off background)
    development_contrast_ok: bool
    fog_margin_ok: bool
    field_orientation_ok: bool     # charged surface must be more negative than developer bias


def evaluate_ladder(
    pcr_applied_v: float,
    developer_bias_v: float,
    exposure_uj_cm2: float,
    pidc: PidcModel | None = None,
    threshold_v: float = V_TH_NOMINAL_V,
    assume_surface_v: float | None = None,
) -> LadderRungs:
    charged = (
        assume_surface_v
        if assume_surface_v is not None
        else dc_roller_surface_potential_v(pcr_applied_v, threshold_v)
    )
    # The characteristic exposure E_a and residual V_r are OPC material
    # properties (anchored to the -600 V datasheet convention); only the
    # starting potential changes with the actual charging outcome.
    model = pidc or model_from_discharge_requirement(0.45, v_charge_v=-600.0)
    model = PidcModel(
        v_charge_v=charged,
        v_residual_v=max(model.v_residual_v, charged) if charged < 0 else model.v_residual_v,
        e_char_uj_cm2=model.e_char_uj_cm2,
        tau_latent_s=model.tau_latent_s,
    )
    latent = model.surface_potential_v(exposure_uj_cm2)
    contrast = developer_bias_v - latent
    fog = charged - developer_bias_v
    return LadderRungs(
        pcr_applied_v=pcr_applied_v,
        charged_surface_v=round(charged, 1),
        exposure_uj_cm2=exposure_uj_cm2,
        latent_surface_v=round(latent, 1),
        developer_bias_v=developer_bias_v,
        development_contrast_v=round(contrast, 1),
        fog_margin_v=round(fog, 1),
        development_contrast_ok=abs(contrast) >= MIN_DEVELOPMENT_CONTRAST_V and contrast < 0.0,
        fog_margin_ok=fog <= -MIN_FOG_MARGIN_V,
        field_orientation_ok=charged < developer_bias_v,
    )


def ladder_summary() -> dict:
    """Assess Rev A as tabled, then the Rev C/D charging options."""
    rev_a_band = []
    for v_th in (V_TH_BAND_V[0], V_TH_NOMINAL_V, V_TH_BAND_V[1]):
        rung = evaluate_ladder(
            pcr_applied_v=-720.0,
            developer_bias_v=-320.0,
            exposure_uj_cm2=0.45,
            threshold_v=v_th,
        )
        rev_a_band.append({"assumed_threshold_v": v_th, **asdict(rung)})

    rev_a_broken = all(not r["field_orientation_ok"] for r in rev_a_band)

    option_a_bias = dc_bias_for_surface_potential_v(-600.0, V_TH_NOMINAL_V)  # about -1160
    option_a_bias = round(option_a_bias - 20.0, 0)  # headroom for threshold drift -> -1180
    option_a = []
    for v_th in (V_TH_BAND_V[0], V_TH_NOMINAL_V, V_TH_BAND_V[1]):
        rung = evaluate_ladder(
            pcr_applied_v=option_a_bias,
            developer_bias_v=-320.0,
            exposure_uj_cm2=0.45,
            threshold_v=v_th,
        )
        option_a.append({"assumed_threshold_v": v_th, **asdict(rung)})

    # AC+DC: surface converges to the DC component when AC pp >= 2 x V_th.
    option_b_dc = -600.0
    option_b = evaluate_ladder(
        pcr_applied_v=option_b_dc,
        developer_bias_v=-320.0,
        exposure_uj_cm2=0.45,
        assume_surface_v=option_b_dc,
    )

    # Developer window across the Fuji OPC sensitivity band: the same bias
    # must work whether the OPC needs 0.15 or 0.80 uJ/cm^2 to discharge.
    sensitivity_band = []
    for e_dd in (0.15, 0.45, 0.80):
        pidc = model_from_discharge_requirement(e_dd, v_charge_v=-600.0)
        rung = evaluate_ladder(
            pcr_applied_v=option_a_bias,
            developer_bias_v=-320.0,
            exposure_uj_cm2=e_dd,  # drive each OPC at its own datasheet energy
            pidc=pidc,
            assume_surface_v=-600.0,
        )
        sensitivity_band.append({"opc_discharge_energy_uj_cm2": e_dd, **asdict(rung)})

    return {
        "revision": "M1-REV-D",
        "model": {
            "dc_contact_charging": "V_surface ~ V_applied - V_th (magnitude), zero below threshold",
            "threshold_v_nominal": V_TH_NOMINAL_V,
            "threshold_v_band": list(V_TH_BAND_V),
            "development_contrast_floor_v": MIN_DEVELOPMENT_CONTRAST_V,
            "fog_margin_floor_v": MIN_FOG_MARGIN_V,
        },
        "rev_a_as_tabled": {
            "pcr_applied_v": -720.0,
            "assumed_charged_surface_v_in_docs": -600.0,
            "band": rev_a_band,
            "verdict_broken": rev_a_broken,
            "verdict": (
                "Rev A cannot print as tabled: -720 V DC on the charge roller "
                "yields roughly -70 to -220 V of drum surface across the "
                "plausible threshold band, never the -600 V the exposure and "
                "developer numbers assume. The developer bias (-320 V) then "
                "sits more negative than the unexposed surface, the background "
                "field reverses, and toner develops everywhere."
            ),
        },
        "rev_c_option_a_dc_only": {
            "pcr_applied_v": option_a_bias,
            "band": option_a,
            "hv_change": (
                "PCR channel range must extend to about -1400 V max; Rev A "
                "tabled -900 V max, so this is a supply redesign, not a set-point tweak."
            ),
            "tradeoffs": "simplest supply; surface potential tracks V_th drift 1:1 (humidity, wear).",
        },
        "rev_c_option_b_ac_dc": {
            "pcr_dc_v": option_b_dc,
            "pcr_ac_physics_min_kvpp": AC_CHARGE_PHYSICS_MIN_KVPP,
            "pcr_ac_spec_kvpp_with_headroom": AC_CHARGE_SPEC_KVPP,
            "rung": asdict(option_b),
            "hv_change": "adds an AC HV stage (~1-2 kHz) superposed on -600 V DC; Rev D specs 1.7 kVpp, not the bare 1.3 kVpp physics floor.",
            "tradeoffs": (
                "surface converges to the DC value and stops tracking V_th "
                "drift; costs an AC stage, adds charging noise/wear "
                "considerations. The generated HV table must match this spec."
            ),
        },
        "developer_window_across_opc_sensitivity_band": sensitivity_band,
        "assumptions": [
            "DC contact-charging relation with a threshold band, not a measured PIDC of a specific drum.",
            "Exposure rung uses the saturating-exponential PIDC anchored to the 0.15-0.80 uJ/cm^2 window.",
            "Floors (150 V contrast, 100 V fog margin) are first-build design floors, not universal constants.",
            "The H1 coupon rig replaces this model with measured values; the ladder structure stays.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(ladder_summary(), indent=2))
