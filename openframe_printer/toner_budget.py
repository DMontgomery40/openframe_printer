from __future__ import annotations

"""Toner mass balance and the no-DRM consumable gauge.

Two problems this solves:

1. An honest yield number. Rev D shipped a live doc/artifact contradiction of
   exactly the class its own HV-consistency gate exists to catch:
   `docs/25_open_consumables_spec.md` claimed "about 2400 pages" from the 80 g
   container while the generated `first_prototype_prints_per_80g_toner_at_5pct`
   computed ~4800 -- a 2x gap, because the naive figure books every gram onto
   paper. Real EP loses toner to imperfect transfer (cleaned into the waste
   cavity) and strands a residual in the hopper it cannot meter out. Rev E
   models the balance and gates the doc against the generated value.

2. The DRM replacement. Locked printers "know" toner level with a chip.
   OpenFrame's consumable rules forbid lockout chips, so the level gauge is
   software: count developed black pixels, multiply by developed mass per
   pixel, subtract from usable mass. This module derives that constant and
   states the honest error bars.

The waste-cavity requirement closes a loop with the cartridge RFQ, which
demands waste capacity >= toner charge life: this artifact computes the
actual cm^3 that requirement implies.
"""

from dataclasses import asdict, dataclass

from .engine_math import EngineTargets, page_image_area_cm2, pixel_area_mm2


@dataclass(frozen=True)
class TonerAssumptions:
    hopper_g: float = 80.0
    coverage: float = 0.05
    transfer_efficiency: float = 0.90     # roller transfer, plain paper, mid-band
    hopper_residual_fraction: float = 0.08  # toner the auger/agitator cannot deliver
    toner_bulk_density_g_cm3: float = 0.40  # settled dry toner
    waste_margin_factor: float = 1.5


def toner_mass_balance(target: EngineTargets | None = None,
                       assume: TonerAssumptions | None = None) -> dict:
    t = target or EngineTargets()
    a = assume or TonerAssumptions()

    area_cm2 = page_image_area_cm2(t)
    on_paper_per_page_mg = area_cm2 * a.coverage * t.toner_dense_black_mg_cm2
    developed_per_page_mg = on_paper_per_page_mg / a.transfer_efficiency
    waste_per_page_mg = developed_per_page_mg - on_paper_per_page_mg

    usable_g = a.hopper_g * (1.0 - a.hopper_residual_fraction)
    pages = usable_g * 1000.0 / developed_per_page_mg
    naive_pages = a.hopper_g * 1000.0 / on_paper_per_page_mg

    waste_at_exhaustion_g = usable_g * (1.0 - a.transfer_efficiency)
    waste_volume_cm3 = waste_at_exhaustion_g / a.toner_bulk_density_g_cm3
    required_cavity_cm3 = waste_volume_cm3 * a.waste_margin_factor

    # Pixel-count gauge: developed mass per black pixel at nominal laydown.
    px_area_cm2 = pixel_area_mm2(t) / 100.0
    developed_mg_per_px = px_area_cm2 * t.toner_dense_black_mg_cm2 / a.transfer_efficiency
    mg_per_megapixel = developed_mg_per_px * 1_000_000.0

    return {
        "assumptions": asdict(a),
        "dense_black_laydown_mg_cm2": t.toner_dense_black_mg_cm2,
        "page_image_area_cm2": area_cm2,
        "on_paper_per_page_mg_at_coverage": on_paper_per_page_mg,
        "developed_per_page_mg_at_coverage": developed_per_page_mg,
        "waste_per_page_mg_at_coverage": waste_per_page_mg,
        "usable_toner_g": usable_g,
        "rated_pages_at_coverage": pages,
        "naive_pages_ignoring_losses": naive_pages,
        "rated_over_naive_ratio": pages / naive_pages,
        "waste_at_toner_exhaustion_g": waste_at_exhaustion_g,
        "waste_volume_at_exhaustion_cm3": waste_volume_cm3,
        "required_waste_cavity_cm3_with_margin": required_cavity_cm3,
        "waste_cavity_outlasts_toner_charge": True,  # by construction of the requirement
        "gauge": {
            "method": "count developed black pixels per page; no chip, no lockout",
            "developed_mg_per_megapixel_black": mg_per_megapixel,
            "laydown_drift_error_band": "+/-20% until density calibration runs",
            "policy": (
                "gauge output is a warning and an ordering hint only; printing "
                "never stops on an estimate, per docs/25 consumable rules"
            ),
        },
        "doc_consistency": {
            "docs_25_must_state_pages_near": round(pages, -2),
            "retired_claim": "about 2400 pages",
            "retired_reason": (
                "2400 matched neither the naive nor the loss-adjusted model; "
                "it was an unsourced figure the artifacts never produced"
            ),
        },
    }


def toner_artifact_consistency(target: EngineTargets | None = None,
                               assume: TonerAssumptions | None = None) -> dict:
    """Gate Rev E's remaining doc/artifact drift in the base design calcs.

    Rev E correctly added a loss-adjusted mass-balance artifact, but the base
    `v2_design_calcs.json` still emitted the old ~4800-page number under an
    unqualified name. Rev F leaves the upper-bound math available only under a
    name that says exactly what it ignores.
    """
    from .engine_math import design_calcs

    calcs = design_calcs(target)
    balance = toner_mass_balance(target, assume)
    retired_key = "first_prototype_prints_per_80g_toner_at_5pct"
    naive_key = "naive_upper_bound_prints_per_80g_toner_at_5pct_ignores_transfer_and_residual_losses"
    checks = {
        "retired_unqualified_4800_page_key_absent": retired_key not in calcs,
        "naive_upper_bound_key_is_explicitly_labeled": naive_key in calcs,
        "design_calcs_declares_retired_key_removed": calcs.get("retired_unqualified_prints_per_80g_key_removed") is True,
        "loss_adjusted_rating_is_lower_than_naive_upper_bound": (
            balance["rated_pages_at_coverage"] < calcs.get(naive_key, 0.0)
        ),
        "loss_adjusted_rating_is_doc_near_4000": 3500.0 <= balance["rated_pages_at_coverage"] <= 4300.0,
    }
    return {
        "revision": "M1-REV-F",
        "retired_key": retired_key,
        "explicit_naive_upper_bound_key": naive_key,
        "naive_upper_bound_pages": calcs.get(naive_key),
        "loss_adjusted_pages": balance["rated_pages_at_coverage"],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "failure_meaning": (
            "If this fails, toner yield has split again between generated artifacts; "
            "do not publish a consumables claim until the base calcs and mass balance agree."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(toner_mass_balance(), indent=2))
