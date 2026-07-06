# 41. Rev E: EP-safe halftoning and the printability lint

The raster path has treated 1-bpp conversion as out of scope. It is not: electrophotography does not print arbitrary bitmaps. An isolated 600 dpi pixel is a ~42 µm latent dot whose fringe field is weak; its development is unstable against drum wear, humidity, and toner charge drift. This is why production EP engines use clustered-dot screens while inkjets can use error diffusion.

Engine: `openframe_printer/halftone.py`. Artifact: `out/v2_halftone_printability.json`.

## The rule, made executable

Minimum stable EP feature is taken as a **2×2 pixel cluster (~85 µm)**. The lint counts black pixels with no black 8-neighbor — features below that size.

Three renderers over a gray ramp (64×64 patches):

| Method | Worst isolated pixels per patch | Verdict |
|---|---:|---|
| 8×8 clustered dot, 2×2-seeded growth | 0 at every tone | default host screen |
| 8×8 Bayer dispersed dither | ~1024 (25% gray) | rejected for EP |
| Floyd–Steinberg error diffusion | ~942 (25% gray) | rejected for EP |

The seeded screen's growth order starts with a 2×2 block at the cell center, so no threshold level can emit a lone pixel by construction.

## The stated cost

A 2×2-seeded 8×8 cell cannot render tones lighter than 4/64 (~6%) within one cell, and the screen frequency is 75 lpi — coarse but honest for a first engine whose development stability is unproven. When the H1 PIDC rig characterizes real dot stability, the screen can be re-derived (smaller seed, angled cells, higher frequency) against measured data instead of a conservative assumption.

## Enforced in code

Model tests prove: the seeded screen emits zero isolated pixels at every level, tone is monotonic in gray level, error diffusion preserves mean tone (so the comparison is fair), and the dispersed comparators genuinely fail the lint. The smoke test requires the artifact and its verdicts.
