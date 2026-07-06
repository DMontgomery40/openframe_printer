# 43. Rev F: halftone floor correction

Engine: `openframe_printer/halftone.py`. Artifacts: `out/v2_halftone_printability.json`, `out/v2_halftone_floor_gate.json`.

## Finding

Rev E made the right architectural choice — clustered-dot halftoning instead of dispersed dots — but the implementation did not actually enforce the physical floor it claimed.

The Rev E raw screen used a 2×2-seeded 8×8 threshold matrix. That sounds safe, but a continuous threshold against rank 0 still emits **one central pixel** for tiny nonzero tones:

| Flat tone | Rev E raw black pixels in 64×64 patch | Rev E isolated pixels | Rev F safe black pixels |
|---:|---:|---:|---:|
| 0.001 | 64 | 64 | 0 |
| 0.005 | 64 | 64 | 0 |
| 0.010 | 64 | 64 | 0 |
| 1/64 | 64 | 64 | 0 |
| 0.020 | 128 | 0 isolated, but 64 sub-2×2 components | 0 |
| 0.050 | 256 | 0 | 0 |
| 4/64 | 256 | 0 | 256 |

That is exactly the unstable 42 µm feature the screen was supposed to forbid.

## Rev F rule

The production screen is now:

1. 8×8 clustered-dot ordered screen,
2. 2×2 seeded nucleus,
3. no emitted tone below 4/64,
4. post-screen connected-component lint that suppresses any feature smaller than the 2×2 physical nucleus.

This is intentionally conservative. Highlights below 6.25% clip to paper white until the H1/PIDC and real developer rig prove a smaller dot survives with the selected OPC, toner, humidity band, and developer bias.

## Research grounding

Electrophotographic printers are a known case where isolated dots can be unstable; clustered-dot screens are used because they group minority pixels into printable features. Good public anchors:

- `https://cv.ulichney.com/papers/2012-Large-Are-Influence%20Electrophotographic-Printers.pdf`
- `https://hammer.purdue.edu/articles/thesis/Model-based_Analysis_and_Design_of_Color_Screen_Sets_for_Clustered-Dot_Periodic_Halftoning_and_Design_of_Monochrome_Screens_Based_on_Direct_Binary_Search_for_Aperiodic_Dispersed-Dot_Halftoning/8968505/files/16415945.pdf`
- `https://research.google/pubs/electro-photographic-model-based-stochastic-clustered-dot-halftoning-with-direct-binary-search/`

## Enforced in code

`halftone_floor_gate()` proves both halves:

- `revE_raw_screen_bug_reproduced: true`
- `revF_screen_passes_floor_gate: true`

`scripts/model_tests.py` now includes explicit negative-control tests for the Rev E partial-seed bug.
