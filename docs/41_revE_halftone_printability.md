# 41. Rev E/F: EP-safe halftoning and the printability lint

The raster path had treated 1-bpp conversion as out of scope. It is not: electrophotography does not print arbitrary bitmaps. An isolated 600 dpi pixel is a ~42 µm latent dot whose fringe field is weak; its development is unstable against drum wear, humidity, and toner charge drift. This is why production EP engines use clustered-dot screens while inkjets can use error diffusion.

Engine: `openframe_printer/halftone.py`. Artifacts: `out/v2_halftone_printability.json`, `out/v2_halftone_floor_gate.json`.

## Rev E rule, and the bug Rev F found

Rev E chose a 2×2-seeded clustered-dot screen. That is the correct direction, but the raw threshold implementation still emitted partial seeds below the claimed 4/64 floor. At tiny nonzero flat tones, rank 0 lit by itself in every 8×8 cell.

Concrete generated negative control:

| Flat tone | Rev E raw isolated pixels per 64×64 patch | Rev F safe isolated pixels |
|---:|---:|---:|
| 0.001 | 64 | 0 |
| 0.005 | 64 | 0 |
| 0.010 | 64 | 0 |
| 1/64 | 64 | 0 |

At 0.020 and 0.030, Rev E's raw screen no longer produced isolated pixels, but it still produced sub-2×2 components. Rev F suppresses those too.

## Rev F production rule

Minimum stable EP feature is taken as a 2×2 pixel cluster (~85 µm). The host rasterizer now uses:

1. 8×8 clustered-dot matrix,
2. 2×2 seed,
3. explicit sub-floor clipping below 4/64,
4. connected-component suppression for features smaller than the 2×2 nucleus.

That costs low highlights: tones below 6.25% clip to paper white until the H1/PIDC and developer rigs prove smaller features survive.

## Dispersed comparators remain rejected

The generated artifact still compares against Bayer and Floyd–Steinberg. They preserve mean tone, but they do it by scattering tiny dots the first EP engine should not promise to develop.

## Research grounding

- `https://cv.ulichney.com/papers/2012-Large-Are-Influence%20Electrophotographic-Printers.pdf`
- `https://hammer.purdue.edu/articles/thesis/Model-based_Analysis_and_Design_of_Color_Screen_Sets_for_Clustered-Dot_Periodic_Halftoning_and_Design_of_Monochrome_Screens_Based_on_Direct_Binary_Search_for_Aperiodic_Dispersed-Dot_Halftoning/8968505/files/16415945.pdf`
- `https://research.google/pubs/electro-photographic-model-based-stochastic-clustered-dot-halftoning-with-direct-binary-search/`

## Enforced in code

Model tests now include the negative control Rev E missed: raw clustered thresholding at 0.001 gray emits isolated pixels. The Rev F safe screen must clip/suppress those features and pass the floor gate.
