# 54. Rev G erase/quench and ghost budget

Earlier revisions modeled charge, exposure, development, transfer, cleaning, and fusing, but left out an explicit **erase/quench station**. That is a process hole, not a cosmetic omission: after toner transfer and cleaning, the photoconductor can still carry residual latent charge. If it re-enters the primary charge station with memory, the expected visible artifact repeats at one drum circumference.

Rev G makes the missing station executable in `openframe_printer/erase_model.py` and `out/v2_erase_ghost_budget.json`.

## Generated finding

With the current 30 mm OPC drum:

```text
one drum circumference: 94.2478 mm
one drum rotation period at 62 mm/s: 1.5201 s
repeat distance at 600 dpi: 2226.3 lines
```

The old as-documented process stack fails the generated gate:

```text
pre_revG_as_documented.verdict = fail_ghost_memory_gate
```

Rev G requirement:

```text
erase station location: after cleaning blade, before primary charge roller
required dose to pull -600 V toward -80 V: 0.5698 µJ/cm²
design erase dose: 0.75 µJ/cm²
margin ratio: 1.316
slot width: 5.0 mm
dwell at 62 mm/s: 80.65 ms
minimum average irradiance: 9.3 µW/cm²
```

The erase dose is deliberately not infinite. The first-build spec requires a bounded energy window: enough margin to quench residual image charge, but not an unbounded exposure that hides OPC fatigue or lamp aging.

## Research basis

The cleaning/erase process is grounded in standard EP process descriptions: toner transfer is not 100% efficient, a cleaning blade removes residual toner, and an erase lamp removes residual latent image before the next cycle.

## Rig gate

Print a high-contrast impulse band, then scan the page at exactly one drum circumference downstream. With erase enabled, residual ghost contrast at the repeat distance must be less than 1% of the source-band contrast. Disable erase for the negative control; the scanner must see the repeat artifact or the test is not sensitive enough.
