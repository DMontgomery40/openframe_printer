# 51. Rev G LED-bar optical MTF gate

Previous revisions treated the LED bar as a 5120-bit timing problem. That is incomplete: a printhead can have the correct emitter count and still blur the latent image if the lens/spot at the OPC plane is too wide.

Generated gate: `out/v2_optical_mtf_budget.json`  
Executable model: `openframe_printer/optical_mtf.py`

## Model

Rev G uses a Gaussian spot model as a first RFQ filter. This is not a claim that the final supplier optics are Gaussian; it is a falsifiable budget that converts 600 dpi into a measurable optical requirement.

For 600 dpi:

```text
pixel pitch = 42.333 µm
Nyquist spatial frequency = 11.811 lp/mm
required MTF at Nyquist = 0.35
```

In the Gaussian approximation, the MTF gate corresponds to:

```text
spot FWHM <= 45.98 µm
neighbor-pixel crosstalk <= 15%
```

## Cases

| Spot FWHM | MTF at 600 dpi Nyquist | Neighbor crosstalk | Gate |
|---:|---:|---:|---|
| 35 µm | 0.544 | 1.7% | pass |
| 40 µm | 0.452 | 4.5% | pass |
| 45 µm | 0.366 | 8.6% | pass |
| 50 µm | 0.289 | 13.7% | fail MTF |
| 60 µm | 0.167 | 25.2% | fail |
| 85 µm | 0.028 | 50.3% | fail hard |

## RFQ change

The LED-bar RFQ now asks for measured MTF at the OPC plane:

```text
MTF >= 0.35 at 12 lp/mm
or equivalent measured spot FWHM <= 45 µm
and one-pixel crosstalk <= 15%
```

This prevents a vendor from satisfying only the electrical pixel count and line-shift timing while delivering optics that cannot hold 600 dpi contrast.

## Research anchors

- Fujifilm Business Innovation's LED printhead technology note explicitly treats high-precision light-intensity control and high-resolution LED printhead optics as core print-quality technology. Rev G's MTF/FWHM gate converts that same physical concern into a first-build acceptance test for OpenFrame.
