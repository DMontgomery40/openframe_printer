# 45. Rev F: toner artifact consistency

Engine: `openframe_printer/toner_budget.py`. Artifact: `out/v2_toner_artifact_consistency.json`.

## Finding

Rev E correctly retired the old **about 2400 pages** consumables claim and introduced the loss-adjusted ~4000-page mass balance. But it left the old naive ~4820-page number alive inside `out/v2_design_calcs.json` under the unqualified key:

```text
first_prototype_prints_per_80g_toner_at_5pct
```

That is the same class of drift Rev D fixed for HV: one artifact says one thing, another artifact still emits the stale number.

## Rev F correction

The base design calcs no longer publish that key. The naive calculation survives only under this deliberately ugly name:

```text
naive_upper_bound_prints_per_80g_toner_at_5pct_ignores_transfer_and_residual_losses
```

The rated number remains owned by `out/v2_toner_mass_balance.json`:

| Quantity | Value |
|---|---:|
| Naive upper bound, no transfer/residual losses | ~4820 pages |
| Loss-adjusted rating, 90% transfer and 8% hopper residual | ~3990 pages |
| Waste cavity with margin | ~28 cm³ |

## Enforced in code

`toner_artifact_consistency()` checks:

- retired unqualified key absent,
- explicit naive upper-bound key present,
- loss-adjusted rating lower than naive upper bound,
- rated pages still near the consumables doc value,
- generated docs continue to point at `v2_toner_mass_balance.json`.
