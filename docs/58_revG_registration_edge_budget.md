# 58. Rev G registration and LED-edge slack budget

OFP1 byte determinism does not make an image land correctly on paper. Rev G adds `openframe_printer/registration_budget.py` and `out/v2_registration_edge_budget.json` to connect page width, LED active width, lateral registration, skew, and line-pitch tolerance.

## Generated finding

At 600 dpi, one pixel / line pitch is 0.042333 mm. The existing 5120-pixel LED bar is:

```text
active width: 216.7467 mm
Letter page width: 216.0000 mm
total lateral margin: 0.7467 mm
slack each side: 0.3733 mm
slack each side in pixels: 8.82 px
passes 1 mm each-side slack goal: false
```

The old ±1 mm registration tolerance is not a print-quality tolerance:

```text
1.0 mm = 23.62 lines at 600 dpi
1.0 mm at the page edge exceeds the current LED edge slack
```

## Rev G options

Rev G provides two honest paths:

```text
Option A: order / design for 5184 active pixels
         active width: 219.456 mm
         slack each side on Letter: 1.728 mm
         raw data-rate increase vs 5120: 1.25%

Option B: keep 5120 pixels only if guaranteed printable width is reduced to 214 mm
         or lateral registration is proven below ±0.25 mm
```

The RFQ should not claim full Letter-width latitude from a 5120-pixel bar unless the mechanical registration evidence is strong enough to earn it.
