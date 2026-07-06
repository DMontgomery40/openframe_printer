# 42. Rev E/F: toner mass balance and no-DRM gauge

Engine: `openframe_printer/toner_budget.py`. Artifacts: `out/v2_toner_mass_balance.json`, `out/v2_toner_artifact_consistency.json`.

## The doc drift Rev E retired

Rev D shipped a live contradiction of exactly the class its own HV-consistency gate exists to catch: `docs/25_open_consumables_spec.md` claimed **"about 2400 pages"** from the 80 g container while generated math computed **~4820**. Neither number was right — the naive figure books every gram of toner onto paper, and the 2400 figure matched no model in the package.

## The Rev F artifact drift still left behind

Rev E correctly added the loss-adjusted mass-balance artifact, but `out/v2_design_calcs.json` still emitted the ~4820-page value under an unqualified key:

```text
first_prototype_prints_per_80g_toner_at_5pct
```

Rev F removes that key. The same math survives only as:

```text
naive_upper_bound_prints_per_80g_toner_at_5pct_ignores_transfer_and_residual_losses
```

## The balance

Per Letter page at 5% coverage and 0.55 mg/cm² dense-black laydown:

| Quantity | Value |
|---|---:|
| Toner on paper | 16.6 mg |
| Toner developed on drum (90% transfer efficiency) | 18.4 mg |
| Toner to waste per page | 1.8 mg |
| Usable hopper mass (8% residual the auger cannot deliver) | 73.6 g |
| **Rated pages** | **~3990** |
| Naive upper bound, no transfer/residual losses | ~4820 |

Losses cost 17% of the naive yield. Mass is conserved per page by construction and by test.

## Waste cavity sizing

At toner exhaustion the waste cavity holds 7.4 g of low-density waste toner (~18.4 cm³ at 0.40 g/cm³ bulk). With a 1.5× margin the cartridge RFQ requirement "waste capacity ≥ toner charge life" concretely means **≥ 28 cm³** of cavity volume.

## The gauge that replaces the chip

Locked printers meter toner with a DRM chip. OpenFrame meters it in software: count developed black pixels, multiply by the developed mass per pixel (**~11 mg per million black pixels** at nominal laydown), subtract from usable mass. Error is ±20% until density calibration runs. Per the consumable rules in doc 25, the gauge output is a warning and ordering hint only — it never stops printing.

## Enforced in code

Model tests pin the loss ratio to `(1 − residual) × transfer efficiency`, verify per-page mass conservation, check the gauge constant against the laydown model, keep the retired 2400-page claim dead, and assert the unqualified ~4820-page key is gone from base design calcs.
