# 03. Engine: monochrome electrophotographic LED

This file is superseded by the v2 Rev A constants in `docs/16_revA_engine_spec.md` and `hardware/design_targets_revA.yaml`. It remains as the plain-English engine overview.

## Rev A summary

| Parameter | Rev A target |
|---|---:|
| Technology | monochrome dry electrophotographic LED |
| Resolution | 600 dpi |
| Speed | 12 ppm Letter |
| Process speed | 62.0 mm/s |
| LED pixels | 5120 |
| LED active width | 216.747 mm |
| OPC drum diameter | 30.0 mm |
| Fuser nominal surface temperature | 178 °C |

## Process steps

1. Charge the OPC drum with the primary charge roller.
2. Expose the charged drum using the stationary LED printbar.
3. Develop the latent image with charged black toner.
4. Transfer toner from drum to paper.
5. Fuse toner to paper with heat and pressure.
6. Clean residual toner into the waste path.

## Why LED instead of laser scanner

A fixed LED bar is easier to package, easier to service, and avoids polygon scanner alignment. The hard part becomes LED uniformity and line timing rather than rotating optics.

## Why monochrome first

Monochrome dry electrophotography avoids inkjet nozzle manufacturing, ink chemistry, color registration, drying, purge stations, and clogged printheads. It gives the first OpenFrame printer the best chance of becoming a real machine.
